import logging

from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks import dump

logger = logging.getLogger(__name__)


def make_dump_path(location_config):  # pragma: no cover
    '''
    Make the dump path from the given location configuration and the name of this hook.
    '''
    return dump.make_database_dump_path(
        location_config.get('borgmatic_source_directory'), 'mongodb_databases'
    )


def dump_databases(databases, log_prefix, location_config, dry_run):
    '''
    Dump the given MongoDB databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given log
    prefix in any log entries. Use the given location configuration dict to construct the
    destination path.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info('{}: Dumping MongoDB databases{}'.format(log_prefix, dry_run_label))

    processes = []
    for database in databases:
        name = database['name']
        dump_filename = dump.make_database_dump_filename(
            make_dump_path(location_config), name, database.get('hostname')
        )
        dump_format = database.get('format', 'archive')

        logger.debug(
            '{}: Dumping MongoDB database {} to {}{}'.format(
                log_prefix, name, dump_filename, dry_run_label
            )
        )
        if dry_run:
            continue

        if dump_format == 'directory':
            dump.create_parent_directory_for_dump(dump_filename)
        else:
            dump.create_named_pipe_for_dump(dump_filename)

        command = build_dump_command(database, dump_filename, dump_format)
        processes.append(execute_command(command, shell=True, run_to_completion=False))

    return processes


def build_dump_command(database, dump_filename, dump_format):
    '''
    Return the mongodump command from a single database configuration.
    '''
    all_databases = database['name'] == 'all'
    command = ['mongodump', '--archive']
    if dump_format == 'directory':
        command.append(dump_filename)
    if 'hostname' in database:
        command.extend(('--host', database['hostname']))
    if 'port' in database:
        command.extend(('--port', str(database['port'])))
    if 'username' in database:
        command.extend(('--username', database['username']))
    if 'password' in database:
        command.extend(('--password', database['password']))
    if 'authentication_database' in database:
        command.extend(('--authenticationDatabase', database['authentication_database']))
    if not all_databases:
        command.extend(('--db', database['name']))
    if 'options' in database:
        command.extend(database['options'].split(' '))
    if dump_format != 'directory':
        command.extend(('>', dump_filename))
    return command


def remove_database_dumps(databases, log_prefix, location_config, dry_run):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the log
    prefix in any log entries. Use the given location configuration dict to construct the
    destination path. If this is a dry run, then don't actually remove anything.
    '''
    dump.remove_database_dumps(make_dump_path(location_config), 'MongoDB', log_prefix, dry_run)


def make_database_dump_pattern(
    databases, log_prefix, location_config, name=None
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a prefix to log with, a location configuration dict,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    return dump.make_database_dump_filename(make_dump_path(location_config), name, hostname='*')


def restore_database_dump(database_config, log_prefix, location_config, dry_run, extract_process):
    '''
    Restore the given MongoDB database from an extract stream. The database is supplied as a
    one-element sequence containing a dict describing the database, as per the configuration schema.
    Use the given log prefix in any log entries. If this is a dry run, then don't actually restore
    anything. Trigger the given active extract process (an instance of subprocess.Popen) to produce
    output to consume.

    If the extract process is None, then restore the dump from the filesystem rather than from an
    extract stream.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    if len(database_config) != 1:
        raise ValueError('The database configuration value is invalid')

    database = database_config[0]
    dump_filename = dump.make_database_dump_filename(
        make_dump_path(location_config), database['name'], database.get('hostname')
    )
    restore_command = build_restore_command(extract_process, database, dump_filename)

    logger.debug(
        '{}: Restoring MongoDB database {}{}'.format(log_prefix, database['name'], dry_run_label)
    )
    if dry_run:
        return

    execute_command_with_processes(
        restore_command,
        [extract_process] if extract_process else [],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout if extract_process else None,
        borg_local_path=location_config.get('local_path', 'borg'),
    )


def build_restore_command(extract_process, database, dump_filename):
    '''
    Return the mongorestore command from a single database configuration.
    '''
    command = ['mongorestore', '--archive']
    if not extract_process:
        command.append(dump_filename)
    if database['name'] != 'all':
        command.extend(('--drop', '--db', database['name']))
    if 'hostname' in database:
        command.extend(('--host', database['hostname']))
    if 'port' in database:
        command.extend(('--port', str(database['port'])))
    if 'username' in database:
        command.extend(('--username', database['username']))
    if 'password' in database:
        command.extend(('--password', database['password']))
    if 'authentication_database' in database:
        command.extend(('--authenticationDatabase', database['authentication_database']))
    return command
