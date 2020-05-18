import logging
import os
import shutil

from borgmatic.borg.create import DEFAULT_BORGMATIC_SOURCE_DIRECTORY

logger = logging.getLogger(__name__)

DATABASE_HOOK_NAMES = ('postgresql_databases', 'mysql_databases')


def make_database_dump_path(borgmatic_source_directory, database_hook_name):
    '''
    Given a borgmatic source directory (or None) and a database hook name, construct a database dump
    path.
    '''
    if not borgmatic_source_directory:
        borgmatic_source_directory = DEFAULT_BORGMATIC_SOURCE_DIRECTORY

    return os.path.join(borgmatic_source_directory, database_hook_name)


def make_database_dump_filename(dump_path, name, hostname=None):
    '''
    Based on the given dump directory path, database name, and hostname, return a filename to use
    for the database dump. The hostname defaults to localhost.

    Raise ValueError if the database name is invalid.
    '''
    if os.path.sep in name:
        raise ValueError('Invalid database name {}'.format(name))

    return os.path.join(os.path.expanduser(dump_path), hostname or 'localhost', name)


def create_parent_directory_for_dump(dump_path):
    '''
    Create a directory to contain the given dump path.
    '''
    os.makedirs(os.path.dirname(dump_path), mode=0o700, exist_ok=True)


def create_named_pipe_for_dump(dump_path):
    '''
    Create a named pipe at the given dump path.
    '''
    create_parent_directory_for_dump(dump_path)
    os.mkfifo(dump_path, mode=0o600)


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

        if os.path.exists(dump_filename):
            if os.path.isdir(dump_filename):
                shutil.rmtree(dump_filename)
            else:
                os.remove(dump_filename)

        dump_file_dir = os.path.dirname(dump_filename)

        if os.path.exists(dump_file_dir) and len(os.listdir(dump_file_dir)) == 0:
            os.rmdir(dump_file_dir)


def convert_glob_patterns_to_borg_patterns(patterns):
    '''
    Convert a sequence of shell glob patterns like "/etc/*" to the corresponding Borg archive
    patterns like "sh:etc/*".
    '''
    return ['sh:{}'.format(pattern.lstrip(os.path.sep)) for pattern in patterns]
