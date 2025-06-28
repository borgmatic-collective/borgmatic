import csv
import itertools
import logging
import os
import pathlib
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
    return dump.make_data_source_dump_path(base_directory, 'postgresql_databases')


def make_environment(database, config, restore_connection_params=None):
    '''
    Make an environment dict from the current environment variables and the given database
    configuration. If restore connection params are given, this is for a restore operation.
    '''
    environment = dict(os.environ)

    try:
        if restore_connection_params:
            environment['PGPASSWORD'] = borgmatic.hooks.credential.parse.resolve_credential(
                (
                    restore_connection_params.get('password')
                    or database.get('restore_password', database['password'])
                ),
                config,
            )
        else:
            environment['PGPASSWORD'] = borgmatic.hooks.credential.parse.resolve_credential(
                database['password'], config
            )
    except (AttributeError, KeyError):
        pass

    if 'ssl_mode' in database:
        environment['PGSSLMODE'] = database['ssl_mode']
    if 'ssl_cert' in database:
        environment['PGSSLCERT'] = database['ssl_cert']
    if 'ssl_key' in database:
        environment['PGSSLKEY'] = database['ssl_key']
    if 'ssl_root_cert' in database:
        environment['PGSSLROOTCERT'] = database['ssl_root_cert']
    if 'ssl_crl' in database:
        environment['PGSSLCRL'] = database['ssl_crl']

    return environment


EXCLUDED_DATABASE_NAMES = ('template0', 'template1')


def database_names_to_dump(database, config, environment, dry_run):
    '''
    Given a requested database config and a configuration dict, return the corresponding sequence of
    database names to dump. In the case of "all" when a database format is given, query for the
    names of databases on the configured host and return them. For "all" without a database format,
    just return a sequence containing "all".
    '''
    requested_name = database['name']

    if requested_name != 'all':
        return (requested_name,)
    if not database.get('format'):
        return ('all',)
    if dry_run:
        return ()

    psql_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('psql_command') or 'psql')
    )
    list_command = (
        psql_command
        + ('--list', '--no-password', '--no-psqlrc', '--csv', '--tuples-only')
        + (('--host', database['hostname']) if 'hostname' in database else ())
        + (('--port', str(database['port'])) if 'port' in database else ())
        + (
            (
                '--username',
                borgmatic.hooks.credential.parse.resolve_credential(database['username'], config),
            )
            if 'username' in database
            else ()
        )
        + (tuple(database['list_options'].split(' ')) if 'list_options' in database else ())
    )
    logger.debug('Querying for "all" PostgreSQL databases to dump')
    list_output = execute_command_and_capture_output(list_command, environment=environment)

    return tuple(
        row[0]
        for row in csv.reader(list_output.splitlines(), delimiter=',', quotechar='"')
        if row[0] not in EXCLUDED_DATABASE_NAMES
    )


def get_default_port(databases, config):  # pragma: no cover
    return 5432


def use_streaming(databases, config):
    '''
    Given a sequence of PostgreSQL database configuration dicts, a configuration dict (ignored),
    return whether streaming will be using during dumps.
    '''
    return any(database.get('format') != 'directory' for database in databases)


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given PostgreSQL databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given
    borgmatic runtime directory to construct the destination path.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the the parent directory of the database dumps to the given patterns list, so the
    dumps actually get backed up.

    Raise ValueError if the databases to dump cannot be determined.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''
    processes = []

    logger.info(f'Dumping PostgreSQL databases{dry_run_label}')

    for database in databases:
        environment = make_environment(database, config)
        dump_path = make_dump_path(borgmatic_runtime_directory)
        dump_database_names = database_names_to_dump(database, config, environment, dry_run)

        if not dump_database_names:
            if dry_run:
                continue

            raise ValueError('Cannot find any PostgreSQL databases to dump.')

        for database_name in dump_database_names:
            dump_format = database.get('format', None if database_name == 'all' else 'custom')
            compression = database.get('compression')
            default_dump_command = 'pg_dumpall' if database_name == 'all' else 'pg_dump'
            dump_command = tuple(
                shlex.quote(part)
                for part in shlex.split(database.get('pg_dump_command') or default_dump_command)
            )
            dump_filename = dump.make_data_source_dump_filename(
                dump_path,
                database_name,
                database.get('hostname'),
                database.get('port'),
            )
            if os.path.exists(dump_filename):
                logger.warning(
                    f'Skipping duplicate dump of PostgreSQL database "{database_name}" to {dump_filename}'
                )
                continue

            command = (
                dump_command
                + (
                    '--no-password',
                    '--clean',
                    '--if-exists',
                )
                + (('--host', shlex.quote(database['hostname'])) if 'hostname' in database else ())
                + (('--port', shlex.quote(str(database['port']))) if 'port' in database else ())
                + (
                    (
                        '--username',
                        shlex.quote(
                            borgmatic.hooks.credential.parse.resolve_credential(
                                database['username'], config
                            )
                        ),
                    )
                    if 'username' in database
                    else ()
                )
                + (('--no-owner',) if database.get('no_owner', False) else ())
                + (('--format', shlex.quote(dump_format)) if dump_format else ())
                + (('--compress', shlex.quote(str(compression))) if compression is not None else ())
                + (('--file', shlex.quote(dump_filename)) if dump_format == 'directory' else ())
                + (
                    tuple(shlex.quote(option) for option in database['options'].split(' '))
                    if 'options' in database
                    else ()
                )
                + (() if database_name == 'all' else (shlex.quote(database_name),))
                # Use shell redirection rather than the --file flag to sidestep synchronization issues
                # when pg_dump/pg_dumpall tries to write to a named pipe. But for the directory dump
                # format in a particular, a named destination is required, and redirection doesn't work.
                + (('>', shlex.quote(dump_filename)) if dump_format != 'directory' else ())
            )

            logger.debug(
                f'Dumping PostgreSQL database "{database_name}" to {dump_filename}{dry_run_label}'
            )
            if dry_run:
                continue

            if dump_format == 'directory':
                dump.create_parent_directory_for_dump(dump_filename)
                execute_command(
                    command,
                    shell=True,  # noqa: S604
                    environment=environment,
                )
            else:
                dump.create_named_pipe_for_dump(dump_filename)
                processes.append(
                    execute_command(
                        command,
                        shell=True,  # noqa: S604
                        environment=environment,
                        run_to_completion=False,
                    )
                )

    if not dry_run:
        patterns.append(
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'postgresql_databases'),
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            )
        )

    return processes


def remove_data_source_dumps(
    databases, config, borgmatic_runtime_directory, dry_run
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic runtime directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(
        make_dump_path(borgmatic_runtime_directory), 'PostgreSQL', dry_run
    )


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
    configuration dict, but the given hook configuration is ignored. The given borgmatic runtime
    directory is used to construct the destination path (used for the directory format). If this is
    a dry run, then don't actually restore anything. Trigger the given active extract process (an
    instance of subprocess.Popen) to produce output to consume.

    If the extract process is None, then restore the dump from the filesystem rather than from an
    extract stream.

    Use the given connection parameters to connect to the database. The connection parameters are
    hostname, port, username, and password.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    hostname = connection_params['hostname'] or data_source.get(
        'restore_hostname', data_source.get('hostname')
    )
    port = str(
        connection_params['port'] or data_source.get('restore_port', data_source.get('port', ''))
    )
    username = borgmatic.hooks.credential.parse.resolve_credential(
        (
            connection_params['username']
            or data_source.get('restore_username', data_source.get('username'))
        ),
        config,
    )

    all_databases = bool(data_source['name'] == 'all')
    dump_filename = dump.make_data_source_dump_filename(
        make_dump_path(borgmatic_runtime_directory),
        data_source['name'],
        data_source.get('hostname'),
    )
    psql_command = tuple(
        shlex.quote(part) for part in shlex.split(data_source.get('psql_command') or 'psql')
    )
    analyze_command = (
        psql_command
        + ('--no-password', '--no-psqlrc', '--quiet')
        + (('--host', hostname) if hostname else ())
        + (('--port', port) if port else ())
        + (('--username', username) if username else ())
        + (('--dbname', data_source['name']) if not all_databases else ())
        + (
            tuple(data_source['analyze_options'].split(' '))
            if 'analyze_options' in data_source
            else ()
        )
        + ('--command', 'ANALYZE')
    )
    use_psql_command = all_databases or data_source.get('format') == 'plain'
    pg_restore_command = tuple(
        shlex.quote(part)
        for part in shlex.split(data_source.get('pg_restore_command') or 'pg_restore')
    )
    restore_command = (
        (psql_command if use_psql_command else pg_restore_command)
        + ('--no-password',)
        + (('--no-psqlrc',) if use_psql_command else ('--if-exists', '--exit-on-error', '--clean'))
        + (('--dbname', data_source['name']) if not all_databases else ())
        + (('--host', hostname) if hostname else ())
        + (('--port', port) if port else ())
        + (('--username', username) if username else ())
        + (('--no-owner',) if data_source.get('no_owner', False) else ())
        + (
            tuple(data_source['restore_options'].split(' '))
            if 'restore_options' in data_source
            else ()
        )
        + (() if extract_process else (str(pathlib.Path(dump_filename)),))
        + tuple(
            itertools.chain.from_iterable(('--schema', schema) for schema in data_source['schemas'])
            if data_source.get('schemas')
            else ()
        )
    )

    environment = make_environment(data_source, config, restore_connection_params=connection_params)

    logger.debug(f"Restoring PostgreSQL database {data_source['name']}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process] if extract_process else [],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout if extract_process else None,
        environment=environment,
    )
    execute_command(analyze_command, environment=environment)
