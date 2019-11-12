import logging
import os

from borgmatic.execute import execute_command
from borgmatic.hooks import dump

DUMP_PATH = '~/.borgmatic/postgresql_databases'
logger = logging.getLogger(__name__)


def dump_databases(databases, log_prefix, dry_run):
    '''
    Dump the given PostgreSQL databases to disk. The databases are supplied as a sequence of dicts,
    one dict describing each database as per the configuration schema. Use the given log prefix in
    any log entries. If this is a dry run, then don't actually dump anything.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info('{}: Dumping PostgreSQL databases{}'.format(log_prefix, dry_run_label))

    for database in databases:
        name = database['name']
        dump_filename = dump.make_database_dump_filename(DUMP_PATH, name, database.get('hostname'))
        all_databases = bool(name == 'all')
        command = (
            ('pg_dumpall' if all_databases else 'pg_dump', '--no-password', '--clean')
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


def remove_database_dumps(databases, log_prefix, dry_run):  # pragma: no cover
    '''
    Remove the database dumps for the given databases. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the log prefix in
    any log entries. If this is a dry run, then don't actually remove anything.
    '''
    dump.remove_database_dumps(DUMP_PATH, databases, 'PostgreSQL', log_prefix, dry_run)


def make_database_dump_patterns(databases, log_prefix, names):
    '''
    Given a sequence of configurations dicts, a prefix to log with, and a sequence of database
    names to match, return the corresponding glob patterns to match the database dumps in an
    archive. An empty sequence of names indicates that the patterns should match all dumps.
    '''
    return [
        dump.make_database_dump_filename(DUMP_PATH, name, hostname='*') for name in (names or ['*'])
    ]


def restore_database_dumps(databases, log_prefix, dry_run):
    '''
    Restore the given PostgreSQL databases from disk. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given log
    prefix in any log entries. If this is a dry run, then don't actually restore anything.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    for database in databases:
        dump_filename = dump.make_database_dump_filename(
            DUMP_PATH, database['name'], database.get('hostname')
        )
        restore_command = (
            ('pg_restore', '--no-password', '--clean', '--if-exists', '--exit-on-error')
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--username', database['username']) if 'username' in database else ())
            + ('--dbname', database['name'])
            + (dump_filename,)
        )
        extra_environment = {'PGPASSWORD': database['password']} if 'password' in database else None
        analyze_command = (
            ('psql', '--no-password', '--quiet')
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--username', database['username']) if 'username' in database else ())
            + ('--dbname', database['name'])
            + ('--command', 'ANALYZE')
        )

        logger.debug(
            '{}: Restoring PostgreSQL database {}{}'.format(
                log_prefix, database['name'], dry_run_label
            )
        )
        if not dry_run:
            execute_command(restore_command, extra_environment=extra_environment)
            execute_command(analyze_command, extra_environment=extra_environment)
