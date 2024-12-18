import logging
import os
import shlex

import borgmatic.config.paths
from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'sqlite_databases')


def use_streaming(databases, config, log_prefix):
    '''
    Given a sequence of SQLite database configuration dicts, a configuration dict (ignored), and a
    log prefix (ignored), return whether streaming will be using during dumps.
    '''
    return any(databases)


def dump_data_sources(
    databases,
    config,
    log_prefix,
    config_paths,
    borgmatic_runtime_directory,
    source_directories,
    dry_run,
):
    '''
    Dump the given SQLite databases to a named pipe. The databases are supplied as a sequence of
    configuration dicts, as per the configuration schema. Use the given borgmatic runtime directory
    to construct the destination path and the given log prefix in any log entries.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the given source directories with the parent directory of the database dumps.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''
    processes = []

    logger.info(f'{log_prefix}: Dumping SQLite databases{dry_run_label}')

    for database in databases:
        database_path = database['path']

        if database['name'] == 'all':
            logger.warning('The "all" database name has no meaning for SQLite databases')
        if not os.path.exists(database_path):
            logger.warning(
                f'{log_prefix}: No SQLite database at {database_path}; an empty database will be created and dumped'
            )

        dump_path = make_dump_path(borgmatic_runtime_directory)
        dump_filename = dump.make_data_source_dump_filename(dump_path, database['name'])

        if os.path.exists(dump_filename):
            logger.warning(
                f'{log_prefix}: Skipping duplicate dump of SQLite database at {database_path} to {dump_filename}'
            )
            continue

        command = (
            'sqlite3',
            shlex.quote(database_path),
            '.dump',
            '>',
            shlex.quote(dump_filename),
        )
        logger.debug(
            f'{log_prefix}: Dumping SQLite database at {database_path} to {dump_filename}{dry_run_label}'
        )
        if dry_run:
            continue

        dump.create_named_pipe_for_dump(dump_filename)
        processes.append(execute_command(command, shell=True, run_to_completion=False))

    if not dry_run:
        source_directories.append(os.path.join(borgmatic_runtime_directory, 'sqlite_databases'))

    return processes


def remove_data_source_dumps(
    databases, config, log_prefix, borgmatic_runtime_directory, dry_run
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic runtime directory to construct the destination path and the log prefix in any log
    entries. If this is a dry run, then don't actually remove anything.
    '''
    dump.remove_data_source_dumps(
        make_dump_path(borgmatic_runtime_directory), 'SQLite', log_prefix, dry_run
    )


def make_data_source_dump_patterns(
    databases, config, log_prefix, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, a prefix to log with, the
    borgmatic runtime directory, and a database name to match, return the corresponding glob
    patterns to match the database dump in an archive.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return (
        dump.make_data_source_dump_filename(make_dump_path('borgmatic'), name, hostname='*'),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), name, hostname='*'
        ),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_source_directory), name, hostname='*'
        ),
    )


def restore_data_source_dump(
    hook_config,
    config,
    log_prefix,
    data_source,
    dry_run,
    extract_process,
    connection_params,
    borgmatic_runtime_directory,
):
    '''
    Restore a database from the given extract stream. The database is supplied as a data source
    configuration dict, but the given hook configuration is ignored. The given log prefix is used
    for any log entries. If this is a dry run, then don't actually restore anything. Trigger the
    given active extract process (an instance of subprocess.Popen) to produce output to consume.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    database_path = connection_params['restore_path'] or data_source.get(
        'restore_path', data_source.get('path')
    )

    logger.debug(f'{log_prefix}: Restoring SQLite database at {database_path}{dry_run_label}')
    if dry_run:
        return

    try:
        os.remove(database_path)
        logger.warning(f'{log_prefix}: Removed existing SQLite database at {database_path}')
    except FileNotFoundError:  # pragma: no cover
        pass

    restore_command = (
        'sqlite3',
        database_path,
    )

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    )
