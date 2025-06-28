import logging
import os
import shlex

import borgmatic.borg.pattern
import borgmatic.config.paths
from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'sqlite_databases')


def get_default_port(databases, config):  # pragma: no cover
    return None  # SQLite doesn't use a port.


def use_streaming(databases, config):
    '''
    Given a sequence of SQLite database configuration dicts, a configuration dict (ignored), return
    whether streaming will be using during dumps.
    '''
    return any(databases)


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given SQLite databases to a named pipe. The databases are supplied as a sequence of
    configuration dicts, as per the configuration schema. Use the given borgmatic runtime directory
    to construct the destination path.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the the parent directory of the database dumps to the given patterns list, so the
    dumps actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''
    processes = []

    logger.info(f'Dumping SQLite databases{dry_run_label}')

    for database in databases:
        database_path = database['path']

        if database['name'] == 'all':
            logger.warning('The "all" database name has no meaning for SQLite databases')
        if not os.path.exists(database_path):
            logger.warning(
                f'No SQLite database at {database_path}; an empty database will be created and dumped'
            )

        dump_path = make_dump_path(borgmatic_runtime_directory)
        dump_filename = dump.make_data_source_dump_filename(dump_path, database['name'])

        if os.path.exists(dump_filename):
            logger.warning(
                f'Skipping duplicate dump of SQLite database at {database_path} to {dump_filename}'
            )
            continue

        sqlite_command = tuple(
            shlex.quote(part) for part in shlex.split(database.get('sqlite_command') or 'sqlite3')
        )
        command = sqlite_command + (
            shlex.quote(database_path),
            '.dump',
            '>',
            shlex.quote(dump_filename),
        )

        logger.debug(
            f'Dumping SQLite database at {database_path} to {dump_filename}{dry_run_label}'
        )
        if dry_run:
            continue

        dump.create_named_pipe_for_dump(dump_filename)
        processes.append(
            execute_command(command, shell=True, run_to_completion=False)  # noqa: S604
        )

    if not dry_run:
        patterns.append(
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'sqlite_databases'),
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            )
        )

    return processes


def remove_data_source_dumps(
    databases, config, borgmatic_runtime_directory, dry_run
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic runtime directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(borgmatic_runtime_directory), 'SQLite', dry_run)


def make_data_source_dump_patterns(
    databases, config, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, the borgmatic runtime directory,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
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
    data_source,
    dry_run,
    extract_process,
    connection_params,
    borgmatic_runtime_directory,
):
    '''
    Restore a database from the given extract stream. The database is supplied as a data source
    configuration dict, but the given hook configuration is ignored. If this is a dry run, then
    don't actually restore anything. Trigger the given active extract process (an instance of
    subprocess.Popen) to produce output to consume.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    database_path = connection_params['restore_path'] or data_source.get(
        'restore_path', data_source.get('path')
    )

    logger.debug(f'Restoring SQLite database at {database_path}{dry_run_label}')
    if dry_run:
        return

    try:
        os.remove(database_path)
        logger.warning(f'Removed existing SQLite database at {database_path}')
    except FileNotFoundError:  # pragma: no cover
        pass

    sqlite_restore_command = tuple(
        shlex.quote(part)
        for part in shlex.split(data_source.get('sqlite_restore_command') or 'sqlite3')
    )
    restore_command = sqlite_restore_command + (shlex.quote(database_path),)
    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    )
