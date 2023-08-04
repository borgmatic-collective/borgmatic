import copy
import logging
import os

from borgmatic.execute import (
    execute_command,
    execute_command_and_capture_output,
    execute_command_with_processes,
)
from borgmatic.hooks import dump

logger = logging.getLogger(__name__)


def make_dump_path(config):  # pragma: no cover
    '''
    Make the dump path from the given configuration dict and the name of this hook.
    '''
    return dump.make_database_dump_path(
        config.get('borgmatic_source_directory'), 'mariadb_databases'
    )


SYSTEM_DATABASE_NAMES = ('information_schema', 'mysql', 'performance_schema', 'sys')


def database_names_to_dump(database, extra_environment, log_prefix, dry_run):
    '''
    Given a requested database config, return the corresponding sequence of database names to dump.
    In the case of "all", query for the names of databases on the configured host and return them,
    excluding any system databases that will cause problems during restore.
    '''
    if database['name'] != 'all':
        return (database['name'],)
    if dry_run:
        return ()

    show_command = (
        ('mariadb',)
        + (tuple(database['list_options'].split(' ')) if 'list_options' in database else ())
        + (('--host', database['hostname']) if 'hostname' in database else ())
        + (('--port', str(database['port'])) if 'port' in database else ())
        + (('--protocol', 'tcp') if 'hostname' in database or 'port' in database else ())
        + (('--user', database['username']) if 'username' in database else ())
        + ('--skip-column-names', '--batch')
        + ('--execute', 'show schemas')
    )
    logger.debug(f'{log_prefix}: Querying for "all" MariaDB databases to dump')
    show_output = execute_command_and_capture_output(
        show_command, extra_environment=extra_environment
    )

    return tuple(
        show_name
        for show_name in show_output.strip().splitlines()
        if show_name not in SYSTEM_DATABASE_NAMES
    )


def execute_dump_command(
    database, log_prefix, dump_path, database_names, extra_environment, dry_run, dry_run_label
):
    '''
    Kick off a dump for the given MariaDB database (provided as a configuration dict) to a named
    pipe constructed from the given dump path and database names. Use the given log prefix in any
    log entries.

    Return a subprocess.Popen instance for the dump process ready to spew to a named pipe. But if
    this is a dry run, then don't actually dump anything and return None.
    '''
    database_name = database['name']
    dump_filename = dump.make_database_dump_filename(
        dump_path, database['name'], database.get('hostname')
    )
    if os.path.exists(dump_filename):
        logger.warning(
            f'{log_prefix}: Skipping duplicate dump of MariaDB database "{database_name}" to {dump_filename}'
        )
        return None

    dump_command = (
        ('mariadb-dump',)
        + (tuple(database['options'].split(' ')) if 'options' in database else ())
        + (('--add-drop-database',) if database.get('add_drop_database', True) else ())
        + (('--host', database['hostname']) if 'hostname' in database else ())
        + (('--port', str(database['port'])) if 'port' in database else ())
        + (('--protocol', 'tcp') if 'hostname' in database or 'port' in database else ())
        + (('--user', database['username']) if 'username' in database else ())
        + ('--databases',)
        + database_names
        + ('--result-file', dump_filename)
    )

    logger.debug(
        f'{log_prefix}: Dumping MariaDB database "{database_name}" to {dump_filename}{dry_run_label}'
    )
    if dry_run:
        return None

    dump.create_named_pipe_for_dump(dump_filename)

    return execute_command(
        dump_command,
        extra_environment=extra_environment,
        run_to_completion=False,
    )


def dump_databases(databases, config, log_prefix, dry_run):
    '''
    Dump the given MariaDB databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given
    configuration dict to construct the destination path and the given log prefix in any log
    entries.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''
    processes = []

    logger.info(f'{log_prefix}: Dumping MariaDB databases{dry_run_label}')

    for database in databases:
        dump_path = make_dump_path(config)
        extra_environment = {'MYSQL_PWD': database['password']} if 'password' in database else None
        dump_database_names = database_names_to_dump(
            database, extra_environment, log_prefix, dry_run
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
                        log_prefix,
                        dump_path,
                        (dump_name,),
                        extra_environment,
                        dry_run,
                        dry_run_label,
                    )
                )
        else:
            processes.append(
                execute_dump_command(
                    database,
                    log_prefix,
                    dump_path,
                    dump_database_names,
                    extra_environment,
                    dry_run,
                    dry_run_label,
                )
            )

    return [process for process in processes if process]


def remove_database_dumps(databases, config, log_prefix, dry_run):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the given
    configuration dict to construct the destination path and the log prefix in any log entries. If
    this is a dry run, then don't actually remove anything.
    '''
    dump.remove_database_dumps(make_dump_path(config), 'MariaDB', log_prefix, dry_run)


def make_database_dump_pattern(databases, config, log_prefix, name=None):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, a prefix to log with, and a
    database name to match, return the corresponding glob patterns to match the database dump in an
    archive.
    '''
    return dump.make_database_dump_filename(make_dump_path(config), name, hostname='*')


def restore_database_dump(
    databases_config, config, log_prefix, database_name, dry_run, extract_process, connection_params
):
    '''
    Restore the given MariaDB database from an extract stream. The databases are supplied as a
    sequence containing one dict describing each database (as per the configuration schema), but
    only the database corresponding to the given database name is restored. Use the given log prefix
    in any log entries. If this is a dry run, then don't actually restore anything. Trigger the
    given active extract process (an instance of subprocess.Popen) to produce output to consume.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    try:
        database = next(
            database_config
            for database_config in databases_config
            if database_config.get('name') == database_name
        )
    except StopIteration:
        raise ValueError(
            f'A database named "{database_name}" could not be found in the configuration'
        )

    hostname = connection_params['hostname'] or database.get(
        'restore_hostname', database.get('hostname')
    )
    port = str(connection_params['port'] or database.get('restore_port', database.get('port', '')))
    username = connection_params['username'] or database.get(
        'restore_username', database.get('username')
    )
    password = connection_params['password'] or database.get(
        'restore_password', database.get('password')
    )

    restore_command = (
        ('mariadb', '--batch')
        + (tuple(database['restore_options'].split(' ')) if 'restore_options' in database else ())
        + (('--host', hostname) if hostname else ())
        + (('--port', str(port)) if port else ())
        + (('--protocol', 'tcp') if hostname or port else ())
        + (('--user', username) if username else ())
    )
    extra_environment = {'MYSQL_PWD': password} if password else None

    logger.debug(f"{log_prefix}: Restoring MariaDB database {database['name']}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment=extra_environment,
    )
