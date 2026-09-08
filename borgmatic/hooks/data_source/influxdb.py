import logging
import os
import shlex

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.hooks.credential.parse
import borgmatic.hooks.data_source.config
from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks.data_source import config as database_config
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'influxdb_databases')


def get_default_port(databases, config):  # pragma: no cover
    return 8086


def use_streaming(databases, config):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


def make_environment(database, config, restore_connection_params=None):
    '''
    Make an environment dict from the current environment variables and the given database
    configuration. If restore connection params are given, this is for a restore operation.

    The InfluxDB API token gets passed via the "INFLUX_TOKEN" environment variable rather than the
    "--token" flag, so that it doesn't show up in the process list for other users to see.
    '''
    environment = dict(os.environ)

    token = database_config.resolve_database_option(
        'password',
        database,
        restore_connection_params,
        restore=restore_connection_params,
    )

    if token:
        environment['INFLUX_TOKEN'] = borgmatic.hooks.credential.parse.resolve_credential(
            token,
            config,
        )

    return environment


def dump_data_sources(
    databases,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Dump the given InfluxDB databases to a directory. The databases are supplied as a sequence of
    dicts, one dict describing each database as per the configuration schema. Use the borgmatic
    runtime directory to construct the destination path. If this is a dry run, then don't actually
    dump anything.

    Also inject a pattern for the parent directory of the database dumps into the given patterns
    list, so the dumps actually get backed up.

    Return an empty sequence, since there are no ongoing dump processes from this hook.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info(f'Dumping InfluxDB databases{dry_run_label}')

    dumps_metadata = []

    for database in databases:
        name = database.get('name')
        dumps_metadata.append(
            borgmatic.actions.restore.Dump(
                'influxdb_databases',
                name,
                database.get('hostname'),
                database.get('port'),
                database.get('label'),
            )
        )

        dump_filename = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory),
            name,
            hostname=database.get('hostname'),
            port=database.get('port'),
            label=database.get('label'),
        )

        logger.debug(
            f'Dumping InfluxDB database to {dump_filename}{dry_run_label}',
        )

        command = build_dump_command(database, dump_filename)
        if dry_run:
            continue

        dump.create_parent_directory_for_dump(dump_filename)
        execute_command(command, environment=make_environment(database, config))

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

    return []


def build_dump_command(database, dump_filename):
    '''
    Given a database configuration dict and a dump filename, return an "influx backup" command as a
    tuple for dumping that database to that filename. The API token isn't included, as it gets passed
    via the environment instead. See make_environment().
    '''
    hostname = database.get('hostname') or 'localhost'
    port = database.get('port') or get_default_port(None, None)  # Use default port if not specified

    # Add protocol prefix based on the tls setting, formatted as protocol://hostname:port.
    protocol = 'https://' if database.get('tls', True) else 'http://'
    host = f'{protocol}{hostname}:{port}'

    skip_verify = database.get('skip_verify')
    http_debug = database.get('http_debug')
    influx_command = tuple(shlex.split(database.get('influx_command') or 'influx'))
    return (
        influx_command
        + ('backup',)
        + (('--skip-verify',) if skip_verify else ())
        + (('--http-debug',) if http_debug else ())
        + ('--host', host)
        + (
            ('--configs-path', database['configurations_path'])
            if 'configurations_path' in database
            else ()
        )
        + (
            ('--active-config', database['active_configuration'])
            if 'active_configuration' in database
            else ()
        )
        + (('--org-id', database['organization_id']) if 'organization_id' in database else ())
        + (
            ('--org', database['organization_name'])
            if 'organization_name' in database and 'organization_id' not in database
            else ()
        )
        + (('--bucket-id', database['bucket_id']) if 'bucket_id' in database else ())
        + (
            ('--bucket', database['name'])
            if database.get('name') not in {None, 'all'} and 'bucket_id' not in database
            else ()
        )
        + (('--compression', database['compression']) if 'compression' in database else ())
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
    Given a sequence of configuration dicts, a configuration dict, the borgmatic runtime directory,
    and a database name, hostname, port, container, and label to match, return the corresponding
    glob patterns to match the database dump in an archive.
    '''
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
    Restore a database from a dump in the given borgmatic runtime directory. The database is
    supplied as a data source configuration dict, but the given hook configuration is ignored. The
    given configuration dict is used to construct the dump path, and the given connection parameters
    override the corresponding database configuration options. If this is a dry run, then don't
    actually restore anything.

    The given extract process is unused, as this hook restores from a dump directory rather than
    from an extract stream.
    '''
    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''

    dump_filename = dump.make_data_source_dump_filename(
        make_dump_path(borgmatic_runtime_directory),
        data_source.get('name'),
        hostname=data_source.get('hostname'),
        port=data_source.get('port'),
        label=data_source.get('label'),
    )

    restore_command = build_restore_command(data_source, dump_filename, connection_params)

    logger.debug(f"Restoring InfluxDB database {data_source.get('name')}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg's local path, as there's no Borg process here for it to apply to: this hook
    # restores from a dump directory that Borg has already extracted rather than from an extract
    # stream.
    tuple(
        execute_command_with_processes(
            restore_command,
            [],
            output_log_level=logging.DEBUG,
            environment=make_environment(
                data_source, config, restore_connection_params=connection_params
            ),
            working_directory=borgmatic.config.paths.get_working_directory(config),
        )
    )


def build_restore_command(database, dump_filename, connection_params):
    '''
    Given a database configuration dict, a dump filename, and a dict of connection parameters
    overriding the database configuration, return an "influx restore" command as a tuple for
    restoring that dump. The API token isn't included, as it gets passed via the environment instead.
    See make_environment().
    '''

    hostname = (
        database_config.resolve_database_option(
            'hostname', database, connection_params, restore=True
        )
        or 'localhost'
    )
    port = (
        database_config.resolve_database_option('port', database, connection_params, restore=True)
        or get_default_port(None, None)  # Use default port if not specified
    )

    # Add protocol prefix based on the tls setting, formatted as protocol://hostname:port.
    protocol = 'https://' if database.get('tls', True) else 'http://'
    host = f'{protocol}{hostname}:{port}'

    organization_id = database.get('organization_id')
    organization_name = database.get('organization_name')
    bucket_id = database.get('bucket_id')
    bucket_name = database.get('name') if database.get('name') != 'all' else None
    restore_bucket = database.get('restore_bucket')
    restore_organization = database.get('restore_organization')
    configurations_path = database.get('configurations_path')
    active_configuration = database.get('active_configuration')
    skip_verify = database.get('skip_verify')
    http_debug = database.get('http_debug')
    full = database.get('full_replace')
    influx_command = tuple(shlex.split(database.get('influx_command') or 'influx'))

    return (
        influx_command
        + ('restore',)
        + ('--host', host)
        + (('--org-id', organization_id) if organization_id else ())
        + (('--org', organization_name) if organization_name and not organization_id else ())
        + (('--bucket-id', bucket_id) if bucket_id else ())
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
