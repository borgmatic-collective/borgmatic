import logging
import os

logger = logging.getLogger(__name__)


def make_database_dump_filename(dump_path, name, hostname=None):
    '''
    Based on the given dump directory path, database name, and hostname, return a filename to use
    for the database dump. The hostname defaults to localhost.

    Raise ValueError if the database name is invalid.
    '''
    if os.path.sep in name:
        raise ValueError('Invalid database name {}'.format(name))

    return os.path.join(os.path.expanduser(dump_path), hostname or 'localhost', name)


def remove_database_dumps(dump_path, databases, database_type_name, log_prefix, dry_run):
    '''
    Remove the database dumps for the given databases in the dump directory path. The databases are
    supplied as a sequence of dicts, one dict describing each database as per the configuration
    schema. Use the name of the database type and the log prefix in any log entries. If this is a
    dry run, then don't actually remove anything.
    '''
    if not databases:
        logger.debug('{}: No {} databases configured'.format(log_prefix, database_type_name))
        return

    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    logger.info(
        '{}: Removing {} database dumps{}'.format(log_prefix, database_type_name, dry_run_label)
    )

    for database in databases:
        dump_filename = make_database_dump_filename(
            dump_path, database['name'], database.get('hostname')
        )

        logger.debug(
            '{}: Removing {} database dump {} from {}{}'.format(
                log_prefix, database_type_name, database['name'], dump_filename, dry_run_label
            )
        )
        if dry_run:
            continue

        os.remove(dump_filename)
        dump_path = os.path.dirname(dump_filename)

        if len(os.listdir(dump_path)) == 0:
            os.rmdir(dump_path)
