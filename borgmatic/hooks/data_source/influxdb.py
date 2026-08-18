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
    return dump.make_data_source_dump_path(base_directory, 'influxdb_databases')


def get_default_port(databases, config):  # pragma: no cover
    return 8086


def use_streaming(databases, config):
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given InfluxDB databases to a named pipe. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the borgmatic
    runtime directory to construct the destination path (used for the directory format and the given
    log prefix in any log entries).

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the the parent directory of the database dumps to the given patterns list, so the
    dumps actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info(f'Dumping InfluxDB databases{dry_run_label}')

    processes = []
    dumps_metadata = []

    for database in databases:
        name = database.get('name')
        dumps_metadata.append(
            borgmatic.actions.restore.Dump(
                'influxdb_databases',
                name,
                database.get('hostname'),
                database.get('port'),
            )
        )

        dump_filename = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory),
            name,
            hostname=database.get('hostname'),
            port=database.get('port'),
        )

        logger.debug(
            f'Dumping InfluxDB database to {dump_filename}{dry_run_label}',
        )

        command = build_dump_command(database, dump_filename)
        if dry_run:
            continue

        logger.debug(
            f'Command: {command}',
        )

        dump.create_parent_directory_for_dump(dump_filename)
        execute_command(command, shell=True)  # noqa: S604

    if not dry_run:
        dump.write_data_source_dumps_metadata(
            borgmatic_runtime_directory, 'influxdb_databases', dumps_metadata
        )
        borgmatic.hooks.data_source.config.inject_pattern(
            patterns,
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'influxdb_databases'),
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            ),
        )

    return processes


def build_dump_command(database, dump_filename):
    '''
    Return the backup command.
    '''
    host = database.get('hostname', 'localhost')
    port = database.get('port') or get_default_port(None, None)  # Use default port if not specified

    if host:
        # Add protocol prefix based on tls setting
        protocol = 'https://' if database.get('tls', True) else 'http://'
        # Format as protocol://hostname:port
        host = f'{protocol}{host}:{port}'

    token = database.get('password')
    skip_verify = database.get('skip_verify')
    http_debug = database.get('http_debug')
    influx_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('influx_command') or 'influx')
    )
    return (
        influx_command
        + ('backup',)
        + (('--skip-verify',) if skip_verify else ())
        + (('--http-debug',) if http_debug else ())
        + (('--host', shlex.quote(str(host))) if host else ())
        + (
            ('--configs-path', shlex.quote(str(database['configurations_path'])))
            if 'configurations_path' in database
            else ()
        )
        + (
            ('--active-config', shlex.quote(str(database['active_configuration'])))
            if 'active_configuration' in database
            else ()
        )
        + (('--token', shlex.quote(str(token))) if token else ())
        + (
            ('--org-id', shlex.quote(str(database['organization_id'])))
            if 'organization_id' in database
            else ()
        )
        + (
            ('--org', shlex.quote(str(database['organization_name'])))
            if 'organization_name' in database and 'organization_id' not in database
            else ()
        )
        + (
            ('--bucket-id', shlex.quote(str(database['bucket_id'])))
            if 'bucket_id' in database
            else ()
        )
        + (
            ('--bucket', shlex.quote(str(database['bucket_name'])))
            if 'bucket_name' in database and 'bucket_id' not in database
            else ()
        )
        + (dump_filename,)
    )


def remove_data_source_dumps(
    databases,
    config,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic_runtime_directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(borgmatic_runtime_directory), 'InfluxDB', dry_run)


def make_data_source_dump_patterns(
    databases,
    config,
    borgmatic_runtime_directory,
    name=None,
    hostname=None,
    port=None,
    container=None,
    label=None,
):
    '''
    Given a sequence of configurations dicts, a configuration dict, the borgmatic runtime directory,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return (
        *(
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
        ),
        *(
            (
                dump.make_data_source_dump_filename(
                    make_dump_path('borgmatic'),
                    name,
                    hostname,
                    port=None,
                    container=container,
                    label=label,
                ),
            )
            if port == get_default_port(databases, config)
            else ()
        ),
        *(
            (
                dump.make_data_source_dump_filename(
                    make_dump_path('borgmatic'),
                    name,
                    hostname,
                    port=get_default_port(databases, config),
                    container=container,
                    label=label,
                ),
            )
            if port is None
            else ()
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
    configuration dict, but the given hook configuration is ignored. The given configuration dict is
    used to construct the destination path, and the given log prefix is used for any log entries. If
    this is a dry run, then don't actually restore anything. Trigger the given active extract
    process (an instance of subprocess.Popen) to produce output to consume.

    If the extract process is None, then restore the dump from the filesystem rather than from an
    extract stream.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    dump_filename = dump.make_data_source_dump_filename(
        make_dump_path(borgmatic_runtime_directory),
        data_source.get('name'),
        data_source.get('hostname'),
        data_source.get('port'),
    )

    restore_command = build_restore_command(
        extract_process, data_source, dump_filename, connection_params
    )

    logger.debug(f"Restoring InfluxDB database {data_source.get('name')}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    tuple(
        execute_command_with_processes(
            restore_command,
            [extract_process] if extract_process else [],
            output_log_level=logging.DEBUG,
            input_file=extract_process.stdout if extract_process else None,
            working_directory=borgmatic.config.paths.get_working_directory(config),
            borg_local_path=config.get('local_path', 'borg'),
        )
    )


def build_restore_command(extract_process, database, dump_filename, connection_params):
    '''
    Return the restore command.
    '''

    host = database.get('hostname', 'localhost')
    port = database.get('port') or get_default_port(None, None)  # Use default port if not specified

    if host:
        # Add protocol prefix based on tls setting
        protocol = 'https://' if database.get('tls', True) else 'http://'
        # Format as protocol://hostname:port
        host = f'{protocol}{host}:{port}'

    token = database.get('password')
    organization_id = database.get('organization_id')
    organization_name = database.get('organization_name')
    bucket_id = database.get('bucket_id')
    bucket_name = database.get('bucket_name')
    restore_bucket = database.get('restore_bucket')
    restore_organization = database.get('restore_organization')
    configurations_path = database.get('configurations_path')
    active_configuration = database.get('active_configuration')
    skip_verify = database.get('skip_verify')
    http_debug = database.get('http_debug')
    full = database.get('full_replace')
    influx_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('influx_command') or 'influx')
    )

    return (
        influx_command
        + ('restore',)
        + (('--host', host) if host else ())
        + (('--token', token) if token else ())
        + (('--org-id', str(organization_id)) if organization_id else ())
        + (('--org', organization_name) if organization_name and not organization_id else ())
        + (('--bucket-id', str(bucket_id)) if bucket_id else ())
        + (('--bucket', bucket_name) if bucket_name and not bucket_id else ())
        + (('--new-bucket', restore_bucket) if restore_bucket else ())
        + (('--new-org', restore_organization) if restore_organization else ())
        + (('--configs-path', configurations_path) if configurations_path else ())
        + (('--active-config', active_configuration) if active_configuration else ())
        + (('--skip-verify',) if skip_verify else ())
        + (('--http-debug',) if http_debug else ())
        + (('--full',) if full else ())
        + (dump_filename,)
    )
