import logging
import os
import shlex
import tempfile

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.hooks.credential.parse
import borgmatic.hooks.data_source.config
from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks.data_source import config as database_config
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'mongodb_databases')


def make_password_config_file_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return os.path.join(base_directory, 'mongodb_config')


def get_default_port(databases, config):  # pragma: no cover
    return 27017


def use_streaming(databases, config):
    '''
    Given a sequence of MongoDB database configuration dicts, a configuration dict (ignored), return
    whether streaming will be using during dumps.
    '''
    return any(database.get('format') != 'directory' for database in databases)


def make_password_config_file_pipe(password):
    '''
    Given a database password, write it as a MongoDB configuration file to an anonymous pipe and
    return its filename. The idea is that this is a more secure way to transmit a password to
    MongoDB than providing it directly on the command-line.

    Do not use the returned value for multiple different command invocations. That will not work
    because each pipe is "used up" once read.
    '''
    logger.debug('Writing MongoDB password to configuration file pipe')

    read_file_descriptor, write_file_descriptor = os.pipe()
    os.write(write_file_descriptor, f'password: {password}'.encode())
    os.close(write_file_descriptor)

    # This plus subprocess.Popen(..., close_fds=False) in execute.py is necessary for the database
    # client child process to inherit the file descriptor.
    os.set_inheritable(read_file_descriptor, True)

    return f'/dev/fd/{read_file_descriptor}'


def make_password_temporary_config_file(password, borgmatic_runtime_directory):
    '''
    Given a database password and the runtime directory, write the password as a MongoDB
    configuration file to a temporary file and return its path. This is a somewhat secure way to
    transmit to MongoDB, at least more secure than passing it directly on the command-line.

    Note that the temporary file isn't cleaned up here, but rather in remove_data_source_dumps()
    below. The intent is that it's available for the full scope of the dump process (which extends
    beyond the dump_data_sources() call).

    The returned path can be used for multiple different command invocations.
    '''
    config_file_path = make_password_config_file_path(borgmatic_runtime_directory)
    os.makedirs(config_file_path, mode=0o700, exist_ok=True)
    password_config_file = tempfile.NamedTemporaryFile(
        'w',
        dir=config_file_path,
        encoding='utf-8',
        delete=False,
    )
    logger.debug(
        f'Writing MongoDB password to temporary configuration file to {password_config_file.name}'
    )

    password_config_file.write(f'password: {password}')
    password_config_file.close()

    return password_config_file.name


def make_password_config_file(database, password, borgmatic_runtime_directory):
    '''
    Given a database configuration dict, a resolved password for that database, and the borgmatic
    runtime directory, write out a password config file for transmitting the password to the MongoDB
    client. Use either a named pipe or a temporary file, depending on the configured password
    transport in the database configuration dict. Defaults to using a named pipe.

    Return None if no password is set.

    Raise ValueError if the password transport is invalid.
    '''
    if not password:
        return None

    password_transport = database.get('password_transport', 'pipe')

    if password_transport == 'pipe':
        return make_password_config_file_pipe(password)

    if password_transport == 'file':
        return make_password_temporary_config_file(password, borgmatic_runtime_directory)

    raise ValueError(f'Invalid password transport: {password_transport}')


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given MongoDB databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the borgmatic
    runtime directory to construct the destination path (used for the directory format.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the the parent directory of the database dumps to the given patterns list, so the
    dumps actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info(f'Dumping MongoDB databases{dry_run_label}')

    processes = []
    dumps_metadata = []

    for database in databases:
        name = database['name']
        dumps_metadata.append(
            borgmatic.actions.restore.Dump(
                'mongodb_databases',
                name,
                database.get('hostname'),
                database.get('port'),
                database.get('label'),
                database.get('container'),
            )
        )

        dump_filename = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory),
            name,
            hostname=database.get('hostname'),
            port=database.get('port'),
            container=database.get('container'),
            label=database.get('label'),
        )
        dump_format = database.get('format', 'archive')

        logger.debug(
            f'Dumping MongoDB database {name} to {dump_filename}{dry_run_label}',
        )
        if dry_run:
            continue

        password = borgmatic.hooks.credential.parse.resolve_credential(
            database.get('password'), config
        )

        command = build_dump_command(
            database,
            config,
            make_password_config_file(database, password, borgmatic_runtime_directory),
            dump_filename,
            dump_format,
        )

        if dump_format == 'directory':
            dump.create_parent_directory_for_dump(dump_filename)
            execute_command(  # noqa: S604
                command,
                shell=True,
                working_directory=borgmatic.config.paths.get_working_directory(config),
            )
        else:
            dump.create_named_pipe_for_dump(dump_filename)
            processes.append(
                execute_command(  # noqa: S604
                    command,
                    shell=True,
                    run_to_completion=False,
                    working_directory=borgmatic.config.paths.get_working_directory(config),
                ),
            )

    if not dry_run:
        dump.write_data_source_dumps_metadata(
            borgmatic_runtime_directory, 'mongodb_databases', dumps_metadata
        )
        borgmatic.hooks.data_source.config.inject_pattern(
            patterns,
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'mongodb_databases'),
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            ),
        )

    return processes


def build_dump_command(database, config, password_config_file_path, dump_filename, dump_format):
    '''
    Given a database configuration dict, a configuration dict, the path of a password config file
    (or None), a dump filename, and a dump format to use, return the custom MongoDB dump command for
    the given database.
    '''
    all_databases = database['name'] == 'all'

    dump_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('mongodump_command') or 'mongodump')
    )
    hostname = database_config.resolve_database_option('hostname', database)
    return (
        dump_command
        + (('--out', shlex.quote(dump_filename)) if dump_format == 'directory' else ())
        + (('--host', shlex.quote(hostname)) if hostname else ())
        + (('--port', shlex.quote(str(database['port']))) if 'port' in database else ())
        + (
            (
                '--username',
                shlex.quote(
                    borgmatic.hooks.credential.parse.resolve_credential(
                        database['username'],
                        config,
                    ),
                ),
            )
            if 'username' in database
            else ()
        )
        + (
            ('--config', shlex.quote(password_config_file_path))
            if password_config_file_path
            else ()
        )
        + (
            (
                '--authenticationDatabase',
                shlex.quote(database['authentication_database']),
            )
            if 'authentication_database' in database
            else ()
        )
        + (('--db', shlex.quote(database['name'])) if not all_databases else ())
        + (
            tuple(shlex.quote(option) for option in database['options'].split(' '))
            if 'options' in database
            else ()
        )
        + (('--archive', '>', shlex.quote(dump_filename)) if dump_format != 'directory' else ())
    )


def remove_data_source_dumps(
    databases,
    config,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic_runtime_directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(borgmatic_runtime_directory), 'MongoDB', dry_run)
    dump.remove_data_source_dumps(
        make_password_config_file_path(borgmatic_runtime_directory),
        'MongoDB password config files for',
        dry_run,
    )


def make_data_source_dump_patterns(
    databases,
    config,
    borgmatic_runtime_directory,
    name=None,
    hostname=None,
    port=None,
    container=None,
    label=None,
):
    '''
    Given a sequence of configurations dicts, a configuration dict, the borgmatic runtime directory,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return (
        *(
            dump.make_data_source_dump_filename(
                make_dump_path('borgmatic'), name, hostname, port, container, label
            ),
            dump.make_data_source_dump_filename(
                make_dump_path(borgmatic_runtime_directory),
                name,
                hostname,
                port,
                container,
                label,
            ),
            dump.make_data_source_dump_filename(
                make_dump_path(borgmatic_source_directory),
                name,
                hostname,
                port,
                container,
                label,
            ),
        ),
        *(
            (
                dump.make_data_source_dump_filename(
                    make_dump_path('borgmatic'),
                    name,
                    hostname,
                    port=None,
                    container=container,
                    label=label,
                ),
            )
            if port == get_default_port(databases, config)
            else ()
        ),
        *(
            (
                dump.make_data_source_dump_filename(
                    make_dump_path('borgmatic'),
                    name,
                    hostname,
                    port=get_default_port(databases, config),
                    container=container,
                    label=label,
                ),
            )
            if port is None
            else ()
        ),
    )


def restore_data_source_dump(
    hook_config,
    config,
    data_source,
    dry_run,
    extract_process,
    connection_params,
    borgmatic_runtime_directory,
):
    '''
    Restore a database from the given extract stream. The database is supplied as a data source
    configuration dict, but the given hook configuration is ignored. The given configuration dict is
    used to construct the destination path. If this is a dry run, then don't actually restore
    anything. Trigger the given active extract process (an instance of subprocess.Popen) to produce
    output to consume.

    If the extract process is None, then restore the dump from the filesystem rather than from an
    extract stream.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    dump_filename = dump.make_data_source_dump_filename(
        make_dump_path(borgmatic_runtime_directory),
        data_source['name'],
        hostname=data_source.get('hostname'),
        port=data_source.get('port'),
        container=data_source.get('container'),
        label=data_source.get('label'),
    )
    password = borgmatic.hooks.credential.parse.resolve_credential(
        database_config.resolve_database_option(
            'password', data_source, connection_params, restore=True
        ),
        config,
    )

    restore_command = build_restore_command(
        extract_process,
        data_source,
        config,
        make_password_config_file(data_source, password, borgmatic_runtime_directory),
        dump_filename,
        connection_params,
    )

    logger.debug(f'Restoring MongoDB database {data_source["name"]}{dry_run_label}')
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    tuple(
        execute_command_with_processes(
            restore_command,
            [extract_process] if extract_process else [],
            output_log_level=logging.DEBUG,
            input_file=extract_process.stdout if extract_process else None,
            working_directory=borgmatic.config.paths.get_working_directory(config),
            borg_local_path=config.get('local_path', 'borg'),
        )
    )


def build_restore_command(
    extract_process, database, config, password_config_file_path, dump_filename, connection_params
):
    '''
    Given an active Borg extract process (if streaming the restore), a database configuration dict,
    a configuration dict, the path of a password config file (or None), a dump filename, and any
    database connection parameters, return the custom MongoDB restore command for the given
    database.
    '''
    hostname = database_config.resolve_database_option(
        'hostname', database, connection_params, restore=True
    )
    port = database_config.resolve_database_option(
        'port', database, connection_params, restore=True
    )
    username = borgmatic.hooks.credential.parse.resolve_credential(
        database_config.resolve_database_option(
            'username', database, connection_params, restore=True
        ),
        config,
    )

    command = [
        shlex.quote(part)
        for part in shlex.split(database.get('mongorestore_command') or 'mongorestore')
    ]

    if extract_process:
        command.append('--archive')
    else:
        command.extend(('--dir', dump_filename))

    if database['name'] != 'all':
        command.extend(('--drop',))

    if hostname:
        command.extend(('--host', hostname))

    if port:
        command.extend(('--port', str(port)))

    if username:
        command.extend(('--username', username))

    if password_config_file_path:
        command.extend(('--config', password_config_file_path))

    if 'authentication_database' in database:
        command.extend(('--authenticationDatabase', database['authentication_database']))

    if 'restore_options' in database:
        command.extend(database['restore_options'].split(' '))

    if database.get('schemas'):
        for schema in database['schemas']:
            command.extend(('--nsInclude', schema))

    return command
