import logging
import os
import shlex

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.hooks.data_source.config
from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'openldap_databases')


def get_default_port(databases, config):  # pragma: no cover
    return None  # OpenLDAP dumps are made locally with slapcat, so there's no port.


def use_streaming(databases, config):
    '''
    Given a sequence of OpenLDAP database configuration dicts, a configuration dict (ignored), return
    whether streaming will be using during dumps.
    '''
    return any(databases)


def build_dump_command(database, dump_filename):
    '''
    Given an OpenLDAP database configuration dict and a dump filename, return the corresponding
    slapcat command as a tuple.

    A database name is an LDAP suffix, selected with slapcat's "-b" flag. There's deliberately no
    support for a name of "all", as slapcat without a selector dumps only the first database rather
    than every one of them. The schema rejects it outright, so it never reaches here.

    Unlike the other database hooks, this command runs without a shell, as slapcat writes to the
    named pipe via its "-l" flag instead of a redirect. So the command parts don't get shell-quoted
    here—there's no shell to inject into, and quoting would corrupt suffixes containing spaces.
    '''
    return (
        *shlex.split(database.get('slapcat_command') or 'slapcat'),
        '-b',
        database['name'],
        '-l',
        dump_filename,
    )


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given OpenLDAP databases to named pipes. The databases are supplied as a sequence of
    configuration dicts, as per the configuration schema. Use the given borgmatic runtime directory
    to construct the destination path.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the parent directory of the database dumps to the given patterns list, so the dumps
    actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''
    processes = []
    dumps_metadata = []

    logger.info(f'Dumping OpenLDAP databases{dry_run_label}')

    for database in databases:
        name = database['name']

        dumps_metadata.append(
            borgmatic.actions.restore.Dump('openldap_databases', name, label=database.get('label'))
        )

        dump_filename = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), name, label=database.get('label')
        )

        if os.path.exists(dump_filename):
            logger.warning(
                f'Skipping duplicate dump of OpenLDAP database "{name}" to {dump_filename}',
            )
            continue

        command = build_dump_command(database, dump_filename)

        logger.debug(f'Dumping OpenLDAP database "{name}" to {dump_filename}{dry_run_label}')
        if dry_run:
            continue

        dump.create_named_pipe_for_dump(dump_filename)
        processes.append(
            execute_command(
                command,
                run_to_completion=False,
                working_directory=borgmatic.config.paths.get_working_directory(config),
            ),
        )

    if not dry_run:
        dump.write_data_source_dumps_metadata(
            borgmatic_runtime_directory, 'openldap_databases', dumps_metadata
        )
        borgmatic.hooks.data_source.config.inject_pattern(
            patterns,
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'openldap_databases'),
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            ),
        )

    return processes


def remove_data_source_dumps(
    databases,
    config,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic runtime directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(borgmatic_runtime_directory), 'OpenLDAP', dry_run)


def make_data_source_dump_patterns(
    databases,
    config,
    borgmatic_runtime_directory,
    name=None,
    hostname=None,
    port=None,
    container=None,
    label=None,
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, the borgmatic runtime directory,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return (
        dump.make_data_source_dump_filename(
            make_dump_path('borgmatic'), name, hostname, port, container, label
        ),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory),
            name,
            hostname,
            port,
            container,
            label,
        ),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_source_directory),
            name,
            hostname,
            port,
            container,
            label,
        ),
    )


def build_restore_command(data_source):
    '''
    Given an OpenLDAP data source configuration dict, return the corresponding slapadd command as a
    tuple.

    As with the dump command, this runs without a shell and so doesn't shell-quote its parts.
    slapadd reads LDIF from standard input whenever "-l" isn't given.
    '''
    return (
        *shlex.split(data_source.get('slapadd_command') or 'slapadd'),
        '-b',
        data_source['name'],
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
    Restore an OpenLDAP database from the given extract stream. The database is supplied as a data
    source configuration dict, but the given hook configuration is ignored. If this is a dry run,
    then don't actually restore anything. Trigger the given active extract process (an instance of
    subprocess.Popen) to produce output to consume.

    slapd must not be running and its database directory must be empty for this to succeed, as
    slapadd refuses to add entries that already exist. borgmatic doesn't stop slapd or clear that
    directory itself, since it may not be responsible for every database living there.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    restore_command = build_restore_command(data_source)

    logger.debug(f'Restoring OpenLDAP database "{data_source["name"]}"{dry_run_label}')

    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    tuple(
        execute_command_with_processes(
            restore_command,
            [extract_process],
            output_log_level=logging.DEBUG,
            input_file=extract_process.stdout,
            working_directory=borgmatic.config.paths.get_working_directory(config),
            borg_local_path=config.get('local_path', 'borg'),
        )
    )
