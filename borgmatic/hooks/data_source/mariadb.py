import copy
import logging
import os
import re
import shlex

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.hooks.credential.parse
from borgmatic.execute import (
    execute_command,
    execute_command_and_capture_output,
    execute_command_with_processes,
)
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'mariadb_databases')


DEFAULTS_EXTRA_FILE_FLAG_PATTERN = re.compile('^--defaults-extra-file=(?P<filename>.*)$')


def parse_extra_options(extra_options):
    '''
    Given an extra options string, split the options into a tuple and return it. Additionally, if
    the first option is "--defaults-extra-file=...", then remove it from the options and return the
    filename.

    So the return value is a tuple of: (parsed options, defaults extra filename).

    The intent is to support downstream merging of multiple "--defaults-extra-file"s, as
    MariaDB/MySQL only allows one at a time.
    '''
    split_extra_options = tuple(shlex.split(extra_options)) if extra_options else ()

    if not split_extra_options:
        return ((), None)

    match = DEFAULTS_EXTRA_FILE_FLAG_PATTERN.match(split_extra_options[0])

    if not match:
        return (split_extra_options, None)

    return (split_extra_options[1:], match.group('filename'))


def make_defaults_file_options(username=None, password=None, defaults_extra_filename=None):
    '''
    Given a database username and/or password, write it to an anonymous pipe and return the flags
    for passing that file descriptor to an executed command. The idea is that this is a more secure
    way to transmit credentials to a database client than using an environment variable.

    If no username or password are given, then return the options for the given defaults extra
    filename (if any). But if there is a username and/or password and a defaults extra filename is
    given, then "!include" it from the generated file, effectively allowing multiple defaults extra
    files.

    Do not use the returned value for multiple different command invocations. That will not work
    because each pipe is "used up" once read.
    '''
    escaped_password = None if password is None else password.replace('\\', '\\\\')

    values = '\n'.join(
        (
            (f'user={username}' if username is not None else ''),
            (f'password="{escaped_password}"' if escaped_password is not None else ''),
        )
    ).strip()

    if not values:
        if defaults_extra_filename:
            return (f'--defaults-extra-file={defaults_extra_filename}',)

        return ()

    fields_message = ' and '.join(
        field_name
        for field_name in (
            (f'username ({username})' if username is not None else None),
            ('password' if password is not None else None),
        )
        if field_name is not None
    )
    include_message = f' (including {defaults_extra_filename})' if defaults_extra_filename else ''
    logger.debug(f'Writing database {fields_message} to defaults extra file pipe{include_message}')

    include = f'!include {defaults_extra_filename}\n' if defaults_extra_filename else ''

    read_file_descriptor, write_file_descriptor = os.pipe()
    os.write(write_file_descriptor, f'{include}[client]\n{values}'.encode('utf-8'))
    os.close(write_file_descriptor)

    # This plus subprocess.Popen(..., close_fds=False) in execute.py is necessary for the database
    # client child process to inherit the file descriptor.
    os.set_inheritable(read_file_descriptor, True)

    return (f'--defaults-extra-file=/dev/fd/{read_file_descriptor}',)


def database_names_to_dump(database, config, username, password, environment, dry_run):
    '''
    Given a requested database config, a configuration dict, a database username and password, an
    environment dict, and whether this is a dry run, return the corresponding sequence of database
    names to dump. In the case of "all", query for the names of databases on the configured host and
    return them, excluding any system databases that will cause problems during restore.
    '''
    if database['name'] != 'all':
        return (database['name'],)
    if dry_run:
        return ()

    mariadb_show_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('mariadb_command') or 'mariadb')
    )
    extra_options, defaults_extra_filename = parse_extra_options(database.get('list_options'))
    password_transport = database.get('password_transport', 'pipe')
    show_command = (
        mariadb_show_command
        + (
            make_defaults_file_options(username, password, defaults_extra_filename)
            if password_transport == 'pipe'
            else ()
        )
        + extra_options
        + (('--host', database['hostname']) if 'hostname' in database else ())
        + (('--port', str(database['port'])) if 'port' in database else ())
        + (('--protocol', 'tcp') if 'hostname' in database or 'port' in database else ())
        + (('--user', username) if username and password_transport == 'environment' else ())
        + (('--ssl',) if database.get('tls') is True else ())
        + (('--skip-ssl',) if database.get('tls') is False else ())
        + ('--skip-column-names', '--batch')
        + ('--execute', 'show schemas')
    )

    logger.debug('Querying for "all" MariaDB databases to dump')

    show_output = execute_command_and_capture_output(show_command, environment=environment)

    return tuple(
        show_name
        for show_name in show_output.strip().splitlines()
        if show_name not in SYSTEM_DATABASE_NAMES
    )


SYSTEM_DATABASE_NAMES = ('information_schema', 'mysql', 'performance_schema', 'sys')


def execute_dump_command(
    database,
    config,
    username,
    password,
    dump_path,
    database_names,
    environment,
    dry_run,
    dry_run_label,
):
    '''
    Kick off a dump for the given MariaDB database (provided as a configuration dict) to a named
    pipe constructed from the given dump path and database name.

    Return a subprocess.Popen instance for the dump process ready to spew to a named pipe. But if
    this is a dry run, then don't actually dump anything and return None.
    '''
    database_name = database['name']
    dump_filename = dump.make_data_source_dump_filename(
        dump_path,
        database['name'],
        database.get('hostname'),
        database.get('port'),
    )

    if os.path.exists(dump_filename):
        logger.warning(
            f'Skipping duplicate dump of MariaDB database "{database_name}" to {dump_filename}'
        )
        return None

    mariadb_dump_command = tuple(
        shlex.quote(part)
        for part in shlex.split(database.get('mariadb_dump_command') or 'mariadb-dump')
    )
    extra_options, defaults_extra_filename = parse_extra_options(database.get('options'))
    password_transport = database.get('password_transport', 'pipe')
    dump_command = (
        mariadb_dump_command
        + (
            make_defaults_file_options(username, password, defaults_extra_filename)
            if password_transport == 'pipe'
            else ()
        )
        + extra_options
        + (('--add-drop-database',) if database.get('add_drop_database', True) else ())
        + (('--host', database['hostname']) if 'hostname' in database else ())
        + (('--port', str(database['port'])) if 'port' in database else ())
        + (('--protocol', 'tcp') if 'hostname' in database or 'port' in database else ())
        + (('--user', username) if username and password_transport == 'environment' else ())
        + (('--ssl',) if database.get('tls') is True else ())
        + (('--skip-ssl',) if database.get('tls') is False else ())
        + ('--databases',)
        + database_names
        + ('--result-file', dump_filename)
    )

    logger.debug(f'Dumping MariaDB database "{database_name}" to {dump_filename}{dry_run_label}')
    if dry_run:
        return None

    dump.create_named_pipe_for_dump(dump_filename)

    return execute_command(
        dump_command,
        environment=environment,
        run_to_completion=False,
    )


def get_default_port(databases, config):  # pragma: no cover
    return 3306


def use_streaming(databases, config):
    '''
    Given a sequence of MariaDB database configuration dicts, a configuration dict (ignored), return
    whether streaming will be using during dumps.
    '''
    return any(databases)


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given MariaDB databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given
    borgmatic runtime directory to construct the destination path.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the the parent directory of the database dumps to the given patterns list, so the
    dumps actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''
    processes = []

    logger.info(f'Dumping MariaDB databases{dry_run_label}')

    for database in databases:
        dump_path = make_dump_path(borgmatic_runtime_directory)
        username = borgmatic.hooks.credential.parse.resolve_credential(
            database.get('username'), config
        )
        password = borgmatic.hooks.credential.parse.resolve_credential(
            database.get('password'), config
        )
        environment = dict(
            os.environ,
            **(
                {'MYSQL_PWD': password}
                if password and database.get('password_transport') == 'environment'
                else {}
            ),
        )
        dump_database_names = database_names_to_dump(
            database, config, username, password, environment, dry_run
        )

        if not dump_database_names:
            if dry_run:
                continue

            raise ValueError('Cannot find any MariaDB databases to dump.')

        if database['name'] == 'all' and database.get('format'):
            for dump_name in dump_database_names:
                renamed_database = copy.copy(database)
                renamed_database['name'] = dump_name
                processes.append(
                    execute_dump_command(
                        renamed_database,
                        config,
                        username,
                        password,
                        dump_path,
                        (dump_name,),
                        environment,
                        dry_run,
                        dry_run_label,
                    )
                )
        else:
            processes.append(
                execute_dump_command(
                    database,
                    config,
                    username,
                    password,
                    dump_path,
                    dump_database_names,
                    environment,
                    dry_run,
                    dry_run_label,
                )
            )

    if not dry_run:
        patterns.append(
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'mariadb_databases'),
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            )
        )

    return [process for process in processes if process]


def remove_data_source_dumps(
    databases, config, borgmatic_runtime_directory, dry_run
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic_runtime_directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(borgmatic_runtime_directory), 'MariaDB', dry_run)


def make_data_source_dump_patterns(
    databases, config, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, the borgmatic runtime directory,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return (
        dump.make_data_source_dump_filename(make_dump_path('borgmatic'), name, hostname='*'),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), name, hostname='*'
        ),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_source_directory), name, hostname='*'
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
    configuration dict, but the given hook configuration is ignored. If this is a dry run, then
    don't actually restore anything. Trigger the given active extract process (an instance of
    subprocess.Popen) to produce output to consume.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    hostname = connection_params['hostname'] or data_source.get(
        'restore_hostname', data_source.get('hostname')
    )
    port = str(
        connection_params['port'] or data_source.get('restore_port', data_source.get('port', ''))
    )
    tls = data_source.get('restore_tls', data_source.get('tls'))
    username = borgmatic.hooks.credential.parse.resolve_credential(
        (
            connection_params['username']
            or data_source.get('restore_username', data_source.get('username'))
        ),
        config,
    )
    password = borgmatic.hooks.credential.parse.resolve_credential(
        (
            connection_params['password']
            or data_source.get('restore_password', data_source.get('password'))
        ),
        config,
    )

    mariadb_restore_command = tuple(
        shlex.quote(part) for part in shlex.split(data_source.get('mariadb_command') or 'mariadb')
    )
    extra_options, defaults_extra_filename = parse_extra_options(data_source.get('restore_options'))
    password_transport = data_source.get('password_transport', 'pipe')
    restore_command = (
        mariadb_restore_command
        + (
            make_defaults_file_options(username, password, defaults_extra_filename)
            if password_transport == 'pipe'
            else ()
        )
        + extra_options
        + ('--batch',)
        + (('--host', hostname) if hostname else ())
        + (('--port', str(port)) if port else ())
        + (('--protocol', 'tcp') if hostname or port else ())
        + (('--user', username) if username and password_transport == 'environment' else ())
        + (('--ssl',) if tls is True else ())
        + (('--skip-ssl',) if tls is False else ())
    )
    environment = dict(
        os.environ,
        **({'MYSQL_PWD': password} if password and password_transport == 'environment' else {}),
    )

    logger.debug(f"Restoring MariaDB database {data_source['name']}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment=environment,
    )
