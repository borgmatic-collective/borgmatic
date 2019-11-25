import glob
import logging
import os

logger = logging.getLogger(__name__)

DATABASE_HOOK_NAMES = ('postgresql_databases', 'mysql_databases')


def make_database_dump_filename(dump_path, name, hostname=None):
    '''
    Based on the given dump directory path, database name, and hostname, return a filename to use
    for the database dump. The hostname defaults to localhost.

    Raise ValueError if the database name is invalid.
    '''
    if os.path.sep in name:
        raise ValueError('Invalid database name {}'.format(name))

    return os.path.join(os.path.expanduser(dump_path), hostname or 'localhost', name)


def flatten_dump_patterns(dump_patterns, names):
    '''
    Given a dict from a database hook name to glob patterns matching the dumps for the named
    databases, flatten out all the glob patterns into a single sequence, and return it.

    Raise ValueError if there are no resulting glob patterns, which indicates that databases are not
    configured in borgmatic's configuration.
    '''
    flattened = [pattern for patterns in dump_patterns.values() for pattern in patterns]

    if not flattened:
        raise ValueError(
            'Cannot restore database(s) {} missing from borgmatic\'s configuration'.format(
                ', '.join(names) or '"all"'
            )
        )

    return flattened


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
        dump_file_dir = os.path.dirname(dump_filename)

        if len(os.listdir(dump_file_dir)) == 0:
            os.rmdir(dump_file_dir)


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


def get_per_hook_database_configurations(hooks, names, dump_patterns):
    '''
    Given the hooks configuration dict as per the configuration schema, a sequence of database
    names to restore, and a dict from database hook name to glob patterns for matching dumps,
    filter down the configuration for just the named databases.

    If there are no named databases given, then find the corresponding database dumps on disk and
    use the database names from their filenames. Additionally, if a database configuration is named
    "all", project out that configuration for each named database.

    Return the results as a dict from database hook name to a sequence of database configuration
    dicts for that database type.

    Raise ValueError if one of the database names cannot be matched to a database in borgmatic's
    database configuration.
    '''
    hook_databases = {
        hook_name: list(
            get_database_configurations(
                hooks.get(hook_name),
                names or get_database_names_from_dumps(dump_patterns[hook_name]),
            )
        )
        for hook_name in DATABASE_HOOK_NAMES
        if hook_name in hooks
    }

    if not names or 'all' in names:
        if not any(hook_databases.values()):
            raise ValueError(
                'Cannot restore database "all", as there are no database dumps in the archive'
            )

        return hook_databases

    found_names = {
        database['name'] for databases in hook_databases.values() for database in databases
    }
    missing_names = sorted(set(names) - found_names)
    if missing_names:
        raise ValueError(
            'Cannot restore database(s) {} missing from borgmatic\'s configuration'.format(
                ', '.join(missing_names)
            )
        )

    return hook_databases
