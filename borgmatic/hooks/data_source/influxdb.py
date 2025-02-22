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
    return dump.make_data_source_dump_path(base_directory, 'influxdb_databases')


def get_default_port(databases, config):  # pragma: no cover
    return 8086


def use_streaming(databases, config):
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return True


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
    log prefix in any log entries.

    Return a sequence of subprocess.Popen instances for the dump processes ready to spew to a named
    pipe. But if this is a dry run, then don't actually dump anything and return an empty sequence.
    Also append the the parent directory of the database dumps to the given patterns list, so the
    dumps actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually dumping anything)' if dry_run else ''

    logger.info(f'Dumping InfluxDB databases{dry_run_label}')

    processes = []
    for database in databases:
        name = database['name']
        dump_filename = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory),
            name,
            database.get('hostname'),
            database.get('port'),
        )

        logger.debug(
            f'Dumping InfluxDB database {name} to {dump_filename}{dry_run_label}',
        )

        command = build_dump_command(database, dump_filename)
        if dry_run:
            continue

        dump.create_named_pipe_for_dump(dump_filename)
        processes.append(execute_command(command, shell=True, run_to_completion=False))

    if not dry_run:
        patterns.append(
            borgmatic.borg.pattern.Pattern(
                os.path.join(borgmatic_runtime_directory, 'influxdb_databases')
            )
        )

    return processes


def build_dump_command(database, dump_filename):
    '''
    Return the backup command.
    '''
    hostname = database.get(
        'dump_hostname', database.get('hostname')
    )
    token = database.get('token')
    skip_verify = database.get('skip_verify')
    http_debug = database.get('http_debug')
    hostname = database.get('hostname')
    influx_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('influx_command') or 'influx')
    )
    return (
        influx_command
        + ('backup',)
        + (('--skip-verify',) if skip_verify else ())
        + (('--http-debug',) if http_debug else ())
        + (('--host', shlex.quote(str(hostname))) if hostname else ())
        + (('--configs-path', shlex.quote(str(database['configs_path']))) if 'configs_path' in database else ())
        + (('--active-config', shlex.quote(str(database['active_config']))) if 'active_config' in database else ())
        + (('--token', shlex.quote(str(token))) if token else ())
        + (('--org-id', shlex.quote(str(database['org_id']))) if 'org_id' in database else ())
        + (('--org', shlex.quote(str(database['org_name']))) if 'org_name' in database else ())
        + (('--bucket-id', shlex.quote(str(database['bucket_id']))) if 'bucket_id' in database else ())
        + (('--bucket', shlex.quote(str(database['bucket_name']))) if 'bucket_name' in database else ())
    )


def remove_data_source_dumps(
    databases, config, borgmatic_runtime_directory, dry_run
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic_runtime_directory to construct the destination path and the log prefix in any log
    entries. If this is a dry run, then don't actually remove anything.
    '''
    dump.remove_data_source_dumps(
        make_dump_path(borgmatic_runtime_directory), 'InfluxDB', dry_run
    )


def make_data_source_dump_patterns(
    databases, config, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, a prefix to log with, the
    borgmatic runtime directory, and a database name to match, return the corresponding glob
    patterns to match the database dump in an archive.
    '''
    return (
        dump.make_data_source_dump_filename(make_dump_path('borgmatic'), name, hostname='*'),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), name, hostname='*'
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
        data_source['name'],
        data_source.get('hostname'),
    )
    restore_command = build_restore_command(
        extract_process, data_source, dump_filename, connection_params
    )

    logger.debug(f"Restoring InfluxDB database {data_source['name']}{dry_run_label}")
    if dry_run:
        return

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command_with_processes(
        restore_command,
        [extract_process] if extract_process else [],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout if extract_process else None,
    )


def build_restore_command(extract_process, database, dump_filename, connection_params):
    '''
    Return the restore command.
    '''
    hostname = connection_params['hostname'] or database.get('hostname')
    token = connection_params['token'] or database.get('token')
    org_id = database.get('org_id')
    org_name = database.get('org_name')
    bucket_name = database.get('bucket_name')
    restore_bucket = database.get('restore_bucket')
    new_org = database.get('new_org')
    configs_path = database.get('configs_path')
    active_config = database.get('active_config')
    skip_verify = database.get('skip_verify')
    http_debug = database.get('http_debug')
    full = database.get('full')
    influx_command = tuple(
        shlex.quote(part) for part in shlex.split(database.get('influx_command') or 'influx')
    )

    return (
        influx_command
        + ('restore',)
        + (('--host', hostname) if hostname else ())
        + (('--token', token) if token else ())
        + (('--org-id', str(org_id)) if org_id else ())
        + (('--org', org_name) if org_name else ())
        + (('--bucket-id', str(bucket_id)) if bucket_id else ())
        + (('--bucket', bucket_name) if bucket_name else ())
        + (('--new-bucket', restore_bucket) if restore_bucket else ())
        + (('--new-org', new_org) if new_org else ())
        + (('--configs-path', configs_path) if configs_path else ())
        + (('--active-config', active_config) if active_config else ())
        + (('--skip-verify',) if skip_verify else ())
        + (('--http-debug',) if http_debug else ())
        + (('--full',) if full else ())
        + (dump_filename,)
    )
