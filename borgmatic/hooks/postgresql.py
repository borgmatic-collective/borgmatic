import logging
import os

from borgmatic.execute import execute_command

DUMP_PATH = '~/.borgmatic/postgresql_databases'
logger = logging.getLogger(__name__)


def dump_databases(databases, config_filename, dry_run):
    '''
    Dump the given PostgreSQL databases to disk. The databases are supplied as a sequence of dicts,
    one dict describing each database as per the configuration schema. Use the given configuration
    filename in any log entries. If this is a dry run, then don't actually dump anything.
    '''
    if not databases:
        logger.debug('{}: No PostgreSQL databases configured'.format(config_filename))
        return

    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info('{}: Dumping PostgreSQL databases{}'.format(config_filename, dry_run_label))

    for database in databases:
        if os.path.sep in database['name']:
            raise ValueError('Invalid database name {}'.format(database['name']))

        dump_path = os.path.join(
            os.path.expanduser(DUMP_PATH), database.get('hostname', 'localhost')
        )
        name = database['name']
        all_databases = bool(name == 'all')
        command = (
            ('pg_dumpall' if all_databases else 'pg_dump', '--no-password', '--clean')
            + ('--file', os.path.join(dump_path, name))
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--username', database['username']) if 'username' in database else ())
            + (() if all_databases else ('--format', database.get('format', 'custom')))
            + (tuple(database['options'].split(' ')) if 'options' in database else ())
            + (() if all_databases else (name,))
        )
        extra_environment = {'PGPASSWORD': database['password']} if 'password' in database else None

        logger.debug(
            '{}: Dumping PostgreSQL database {}{}'.format(config_filename, name, dry_run_label)
        )
        if not dry_run:
            os.makedirs(dump_path, mode=0o700, exist_ok=True)
            execute_command(command, extra_environment=extra_environment)


def remove_database_dumps(databases, config_filename, dry_run):
    '''
    Remove the database dumps for the given databases. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given
    configuration filename in any log entries. If this is a dry run, then don't actually remove
    anything.
    '''
    if not databases:
        logger.debug('{}: No PostgreSQL databases configured'.format(config_filename))
        return

    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    logger.info('{}: Removing PostgreSQL database dumps{}'.format(config_filename, dry_run_label))

    for database in databases:
        if os.path.sep in database['name']:
            raise ValueError('Invalid database name {}'.format(database['name']))

        name = database['name']
        dump_path = os.path.join(
            os.path.expanduser(DUMP_PATH), database.get('hostname', 'localhost')
        )
        dump_filename = os.path.join(dump_path, name)

        logger.debug(
            '{}: Remove PostgreSQL database dump {} from {}{}'.format(
                config_filename, name, dump_filename, dry_run_label
            )
        )
        if dry_run:
            continue

        os.remove(dump_filename)
        if len(os.listdir(dump_path)) == 0:
            os.rmdir(dump_path)
