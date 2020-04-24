import logging
import os

from borgmatic.execute import execute_command
from borgmatic.hooks import dump

logger = logging.getLogger(__name__)


def make_dump_path(location_config):  # pragma: no cover
    '''
    Make the dump path from the given location configuration and the name of this hook.
    '''
    return dump.make_database_dump_path(
        location_config.get('borgmatic_source_directory'), 'postgresql_databases'
    )


def dump_databases(databases, log_prefix, location_config, dry_run):
    '''
    Dump the given PostgreSQL databases to disk. The databases are supplied as a sequence of dicts,
    one dict describing each database as per the configuration schema. Use the given log prefix in
    any log entries. Use the given location configuration dict to construct the destination path. If
    this is a dry run, then don't actually dump anything.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info('{}: Dumping PostgreSQL databases{}'.format(log_prefix, dry_run_label))

    for database in databases:
        name = database['name']
        dump_filename = dump.make_database_dump_filename(
            make_dump_path(location_config), name, database.get('hostname')
        )
        all_databases = bool(name == 'all')
        command = (
            (
                'pg_dumpall' if all_databases else 'pg_dump',
                '--no-password',
                '--clean',
                '--if-exists',
            )
            + ('--file', dump_filename)
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--username', database['username']) if 'username' in database else ())
            + (() if all_databases else ('--format', database.get('format', 'custom')))
            + (tuple(database['options'].split(' ')) if 'options' in database else ())
            + (() if all_databases else (name,))
        )
        extra_environment = {'PGPASSWORD': database['password']} if 'password' in database else None

        logger.debug(
            '{}: Dumping PostgreSQL database {} to {}{}'.format(
                log_prefix, name, dump_filename, dry_run_label
            )
        )
        if not dry_run:
            os.makedirs(os.path.dirname(dump_filename), mode=0o700, exist_ok=True)
            execute_command(command, extra_environment=extra_environment)


def remove_database_dumps(databases, log_prefix, location_config, dry_run):  # pragma: no cover
    '''
    Remove the database dumps for the given databases. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the log prefix in
    any log entries. Use the given location configuration dict to construct the destination path. If
    this is a dry run, then don't actually remove anything.
    '''
    dump.remove_database_dumps(
        make_dump_path(location_config), databases, 'PostgreSQL', log_prefix, dry_run
    )


def make_database_dump_patterns(databases, log_prefix, location_config, names):
    '''
    Given a sequence of configurations dicts, a prefix to log with, a location configuration dict,
    and a sequence of database names to match, return the corresponding glob patterns to match the
    database dumps in an archive. An empty sequence of names indicates that the patterns should
    match all dumps.
    '''
    return [
        dump.make_database_dump_filename(make_dump_path(location_config), name, hostname='*')
        for name in (names or ['*'])
    ]


def restore_database_dumps(databases, log_prefix, location_config, dry_run):
    '''
    Restore the given PostgreSQL databases from disk. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given log
    prefix in any log entries. Use the given location configuration dict to construct the
    destination path. If this is a dry run, then don't actually restore anything.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    for database in databases:
        dump_filename = dump.make_database_dump_filename(
            make_dump_path(location_config), database['name'], database.get('hostname')
        )
        all_databases = bool(database['name'] == 'all')
        analyze_command = (
            ('psql', '--no-password', '--quiet')
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--username', database['username']) if 'username' in database else ())
            + (('--dbname', database['name']) if not all_databases else ())
            + ('--command', 'ANALYZE')
        )
        restore_command = (
            ('psql' if all_databases else 'pg_restore', '--no-password')
            + (
                ('--if-exists', '--exit-on-error', '--clean', '--dbname', database['name'])
                if not all_databases
                else ()
            )
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--username', database['username']) if 'username' in database else ())
            + (('-f', dump_filename) if all_databases else (dump_filename,))
        )
        extra_environment = {'PGPASSWORD': database['password']} if 'password' in database else None

        logger.debug(
            '{}: Restoring PostgreSQL database {}{}'.format(
                log_prefix, database['name'], dry_run_label
            )
        )
        if not dry_run:
            execute_command(restore_command, extra_environment=extra_environment)
            execute_command(analyze_command, extra_environment=extra_environment)
