import logging
import shlex

from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks import dump

logger = logging.getLogger(__name__)


def make_dump_path(config):  # pragma: no cover
    '''
    Make the dump path from the given configuration dict and the name of this hook.
    '''
    return dump.make_data_source_dump_path(
        config.get('borgmatic_source_directory'), 'mongodb_databases'
    )


def use_streaming(databases, config, log_prefix):
    '''
    Given a sequence of MongoDB database configuration dicts, a configuration dict (ignored), and a
    log prefix (ignored), return whether streaming will be using during dumps.
    '''
    return any(database.get('format') != 'directory' for database in databases)


def dump_data_sources(databases, config, log_prefix, dry_run):
    '''
    Dump the given MongoDB databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the configuration
    dict to construct the destination path and the given log prefix in any log entries.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info(f'{log_prefix}: Dumping MongoDB databases{dry_run_label}')

    processes = []
    for database in databases:
        name = database['name']
        dump_filename = dump.make_data_source_dump_filename(
            make_dump_path(config), name, database.get('hostname')
        )
        dump_format = database.get('format', 'archive')

        logger.debug(
            f'{log_prefix}: Dumping MongoDB database {name} to {dump_filename}{dry_run_label}',
        )
        if dry_run:
            continue

        command = build_dump_command(database, dump_filename, dump_format)

        if dump_format == 'directory':
            dump.create_parent_directory_for_dump(dump_filename)
            execute_command(command, shell=True)
        else:
            dump.create_named_pipe_for_dump(dump_filename)
            processes.append(execute_command(command, shell=True, run_to_completion=False))

    return processes


def build_dump_command(database, dump_filename, dump_format):
    '''
    Return the mongodump command from a single database configuration.
    '''
    all_databases = database['name'] == 'all'

    return (
        ('mongodump',)
        + (('--out', shlex.quote(dump_filename)) if dump_format == 'directory' else ())
        + (('--host', shlex.quote(database['hostname'])) if 'hostname' in database else ())
        + (('--port', shlex.quote(str(database['port']))) if 'port' in database else ())
        + (('--username', shlex.quote(database['username'])) if 'username' in database else ())
        + (('--password', shlex.quote(database['password'])) if 'password' in database else ())
        + (
            ('--authenticationDatabase', shlex.quote(database['authentication_database']))
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


def remove_data_source_dumps(databases, config, log_prefix, dry_run):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the log
    prefix in any log entries. Use the given configuration dict to construct the destination path.
    If this is a dry run, then don't actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(config), 'MongoDB', log_prefix, dry_run)


def make_data_source_dump_pattern(databases, config, log_prefix, name=None):  # pragma: no cover
    '''
    Given a sequence of database configurations dicts, a configuration dict, a prefix to log with,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    return dump.make_data_source_dump_filename(make_dump_path(config), name, hostname='*')


def restore_data_source_dump(
    hook_config, config, log_prefix, data_source, dry_run, extract_process, connection_params
):
    '''
    Restore a database from the given extract stream. The database is supplied as a data source
    configuration dict, but the given hook configuration is ignored. The given configuration dict is
    used to construct the destination path, and the given log prefix is used for any log entries. If
    this is a dry run, then don't actually restore anything. Trigger the given active extract
    process (an instance of subprocess.Popen) to produce output to consume.

    If the extract process is None, then restore the dump from the filesystem rather than from an
    extract stream.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    dump_filename = dump.make_data_source_dump_filename(
        make_dump_path(config), data_source['name'], data_source.get('hostname')
    )
    restore_command = build_restore_command(
        extract_process, data_source, dump_filename, connection_params
    )

    logger.debug(f"{log_prefix}: Restoring MongoDB database {data_source['name']}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process] if extract_process else [],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout if extract_process else None,
    )


def build_restore_command(extract_process, database, dump_filename, connection_params):
    '''
    Return the mongorestore command from a single database configuration.
    '''
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

    command = ['mongorestore']
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
    if password:
        command.extend(('--password', password))
    if 'authentication_database' in database:
        command.extend(('--authenticationDatabase', database['authentication_database']))
    if 'restore_options' in database:
        command.extend(database['restore_options'].split(' '))
    if database.get('schemas'):
        for schema in database['schemas']:
            command.extend(('--nsInclude', schema))

    return command
