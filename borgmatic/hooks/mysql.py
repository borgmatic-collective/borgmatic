import logging
import os

from borgmatic.execute import execute_command
from borgmatic.hooks import dump

DUMP_PATH = '~/.borgmatic/mysql_databases'
logger = logging.getLogger(__name__)


def dump_databases(databases, log_prefix, dry_run):
    '''
    Dump the given MySQL/MariaDB databases to disk. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the given log
    prefix in any log entries. If this is a dry run, then don't actually dump anything.
    '''
    if not databases:
        logger.debug('{}: No MySQL databases configured'.format(log_prefix))
        return

    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info('{}: Dumping MySQL databases{}'.format(log_prefix, dry_run_label))

    for database in databases:
        name = database['name']
        dump_filename = dump.make_database_dump_filename(DUMP_PATH, name, database.get('hostname'))
        command = (
            ('mysqldump', '--add-drop-database')
            + (('--host', database['hostname']) if 'hostname' in database else ())
            + (('--port', str(database['port'])) if 'port' in database else ())
            + (('--protocol', 'tcp') if 'hostname' in database or 'port' in database else ())
            + (('--user', database['username']) if 'username' in database else ())
            + (tuple(database['options'].split(' ')) if 'options' in database else ())
            + (('--all-databases',) if name == 'all' else ('--databases', name))
        )
        extra_environment = {'MYSQL_PWD': database['password']} if 'password' in database else None

        logger.debug(
            '{}: Dumping MySQL database {} to {}{}'.format(
                log_prefix, name, dump_filename, dry_run_label
            )
        )
        if not dry_run:
            os.makedirs(os.path.dirname(dump_filename), mode=0o700, exist_ok=True)
            execute_command(
                command, output_file=open(dump_filename, 'w'), extra_environment=extra_environment
            )


def remove_database_dumps(databases, log_prefix, dry_run):
    '''
    Remove the database dumps for the given databases. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the log prefix in
    any log entries. If this is a dry run, then don't actually remove anything.
    '''
    dump.remove_database_dumps(DUMP_PATH, databases, 'MySQL', log_prefix, dry_run)
