import logging
import os
import shutil

from borgmatic.borg.state import DEFAULT_BORGMATIC_SOURCE_DIRECTORY

logger = logging.getLogger(__name__)

DATA_SOURCE_HOOK_NAMES = (
    'mariadb_databases',
    'mysql_databases',
    'mongodb_databases',
    'postgresql_databases',
    'sqlite_databases',
)


def make_data_source_dump_path(borgmatic_source_directory, data_source_hook_name):
    '''
    Given a borgmatic source directory (or None) and a data source hook name, construct a data
    source dump path.
    '''
    if not borgmatic_source_directory:
        borgmatic_source_directory = DEFAULT_BORGMATIC_SOURCE_DIRECTORY

    return os.path.join(borgmatic_source_directory, data_source_hook_name)


def make_data_source_dump_filename(dump_path, name, hostname=None):
    '''
    Based on the given dump directory path, data source name, and hostname, return a filename to use
    for the data source dump. The hostname defaults to localhost.

    Raise ValueError if the data source name is invalid.
    '''
    if os.path.sep in name:
        raise ValueError(f'Invalid data source name {name}')

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


def remove_data_source_dumps(dump_path, data_source_type_name, log_prefix, dry_run):
    '''
    Remove all data source dumps in the given dump directory path (including the directory itself).
    If this is a dry run, then don't actually remove anything.
    '''
    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    logger.debug(f'{log_prefix}: Removing {data_source_type_name} data source dumps{dry_run_label}')

    expanded_path = os.path.expanduser(dump_path)

    if dry_run:
        return

    if os.path.exists(expanded_path):
        shutil.rmtree(expanded_path)


def convert_glob_patterns_to_borg_patterns(patterns):
    '''
    Convert a sequence of shell glob patterns like "/etc/*" to the corresponding Borg archive
    patterns like "sh:etc/*".
    '''
    return [f'sh:{pattern.lstrip(os.path.sep)}' for pattern in patterns]
