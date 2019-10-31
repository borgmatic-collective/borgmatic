import glob
import logging
import os

from borgmatic.execute import execute_command

DUMP_PATH = '~/.borgmatic/postgresql_databases'
logger = logging.getLogger(__name__)


def make_database_dump_filename(name, hostname=None):
    '''
    Based on the given database name and hostname, return a filename to use for the database dump.

    Raise ValueError if the database name is invalid.
    '''
    if os.path.sep in name:
        raise ValueError('Invalid database name {}'.format(name))

    return os.path.join(os.path.expanduser(DUMP_PATH), hostname or 'localhost', name)


def dump_databases(databases, log_prefix, dry_run):
    '''
    Dump the given PostgreSQL databases to disk. The databases are supplied as a sequence of dicts,
    one dict describing each database as per the configuration schema. Use the given log prefix in
    any log entries. If this is a dry run, then don't actually dump anything.
    '''
    if not databases:
        logger.debug('{}: No PostgreSQL databases configured'.format(log_prefix))
        return

    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info('{}: Dumping PostgreSQL databases{}'.format(log_prefix, dry_run_label))

    for database in databases:
        name = database['name']
        dump_filename = make_database_dump_filename(name, database.get('hostname'))
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

        logger.debug('{}: Dumping PostgreSQL database {}{}'.format(log_prefix, name, dry_run_label))
        if not dry_run:
            os.makedirs(os.path.dirname(dump_filename), mode=0o700, exist_ok=True)
            execute_command(command, extra_environment=extra_environment)


def remove_database_dumps(databases, log_prefix, dry_run):
    '''
    Remove the database dumps for the given databases. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the log prefix in
    any log entries. If this is a dry run, then don't actually remove anything.
    '''
    if not databases:
        logger.debug('{}: No PostgreSQL databases configured'.format(log_prefix))
        return

    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    logger.info('{}: Removing PostgreSQL database dumps{}'.format(log_prefix, dry_run_label))

    for database in databases:
        dump_filename = make_database_dump_filename(database['name'], database.get('hostname'))

        logger.debug(
            '{}: Removing PostgreSQL database dump {} from {}{}'.format(
                log_prefix, database['name'], dump_filename, dry_run_label
            )
        )
        if dry_run:
            continue

        os.remove(dump_filename)
        dump_path = os.path.dirname(dump_filename)

        if len(os.listdir(dump_path)) == 0:
            os.rmdir(dump_path)


def make_database_dump_patterns(names):
    '''
    Given a sequence of database names, return the corresponding glob patterns to match the database
    dumps in an archive. An empty sequence of names indicates that the patterns should match all
    dumps.
    '''
    return [make_database_dump_filename(name, hostname='*') for name in (names or ['*'])]


def convert_glob_patterns_to_borg_patterns(patterns):
    '''
    Convert a sequence of shell glob patterns like "/etc/*" to the corresponding Borg archive
    patterns like "sh:etc/*".
    '''
    return ['sh:{}'.format(pattern.lstrip(os.path.sep)) for pattern in patterns]


def get_database_names_from_dumps(patterns):
    '''
    Given a sequence of database dump patterns, find the corresponding database dumps on disk and
    return the database names from their filenames.
    '''
    return [os.path.basename(dump_path) for pattern in patterns for dump_path in glob.glob(pattern)]


def get_database_configurations(databases, names):
    '''
    Given the full database configuration dicts as per the configuration schema, and a sequence of
    database names, filter down and yield the configuration for just the named databases.
    Additionally, if a database configuration is named "all", project out that configuration for
    each named database.

    Raise ValueError if one of the database names cannot be matched to a database in borgmatic's
    database configuration.
    '''
    named_databases = {database['name']: database for database in databases}

    for name in names:
        database = named_databases.get(name)
        if database:
            yield database
            continue

        if 'all' in named_databases:
            yield {**named_databases['all'], **{'name': name}}
            continue

        raise ValueError(
            'Cannot restore database "{}", as it is not defined in borgmatic\'s configuration'.format(
                name
            )
        )


def restore_database_dumps(databases, log_prefix, dry_run):
    '''
    Restore the given PostgreSQL databases from disk. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given log
    prefix in any log entries. If this is a dry run, then don't actually restore anything.
    '''
    if not databases:
        logger.debug('{}: No PostgreSQL databases configured'.format(log_prefix))
        return

    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    for database in databases:
        dump_filename = make_database_dump_filename(database['name'], database.get('hostname'))
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
