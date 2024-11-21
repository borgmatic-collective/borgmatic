import logging
import os
import shlex
import subprocess

import borgmatic.config.paths
import borgmatic.execute

logger = logging.getLogger(__name__)


def use_streaming(hook_config, config, log_prefix):
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


BORGMATIC_SNAPSHOT_PREFIX = 'borgmatic-'


def dump_data_sources(
    hook_config,
    config,
    log_prefix,
    borgmatic_runtime_directory,
    source_directories,
    dry_run,
):
    '''
    Given a ZFS configuration dict, a configuration dict, a log prefix, the borgmatic runtime
    directory, the configured source directories, and whether this is a dry run, auto-detect and
    snapshot any ZFS dataset mount points listed in the given source directories. Also update those
    source directories, replacing dataset mount points with corresponding snapshot directories. Use
    the log prefix in any log entries.

    Return an empty sequence, since there are no ongoing dump processes.

    If this is a dry run or ZFS isn't enabled, then don't actually snapshot anything.
    '''
    dry_run_label = ' (dry run; not actually snapshotting anything)' if dry_run else ''
    logger.info(f'{log_prefix}: Snapshotting ZFS datasets{dry_run_label}')

    # List ZFS datasets to get their mount points.
    zfs_command = hook_config.get('zfs_command', 'zfs')
    list_command = (
        zfs_command,
        'list',
        '-H',
        '-t',
        'filesystem',
        '-o',
        'name,mountpoint',
    )
    list_output = borgmatic.execute.execute_command_and_capture_output(list_command)
    mount_point_to_dataset_name = {
        mount_point: dataset_name
        for line in list_output.splitlines()
        for (dataset_name, mount_point) in (line.rstrip().split('\t'),)
    }

    # Find the intersection between those mount points and the configured borgmatic source
    # directories, the idea being that these are the requested datasets to snapshot.
    requested_mount_point_to_dataset_name = {
        source_directory: dataset_name
        for source_directory in source_directories
        for dataset_name in (mount_point_to_dataset_name.get(source_directory),)
        if dataset_name
    }

    # TODO: Also maybe support datasets with property torsion.org.borgmatic:backup even if not
    # listed in source directories?

    # Snapshot each dataset, rewriting source directories to use the snapshot paths.
    snapshot_paths = []
    snapshot_name = f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}'

    for mount_point, dataset_name in requested_mount_point_to_dataset_name.items():
        full_snapshot_name = f'{dataset_name}@{snapshot_name}'
        logger.debug(f'{log_prefix}: Creating ZFS snapshot {full_snapshot_name}{dry_run_label}')

        if not dry_run:
            borgmatic.execute.execute_command(
                (
                    zfs_command,
                    'snapshot',
                    '-r',
                    full_snapshot_name,
                ),
                output_log_level=logging.DEBUG,
            )

        # Mount the snapshot into a particular named temporary directory so that the snapshot ends
        # up in the Borg archive at the "original" dataset mount point path.
        snapshot_path = os.path.join(
            os.path.normpath(borgmatic_runtime_directory),
            'zfs_snapshots',
            '.',
            mount_point.lstrip(os.path.sep),
        )
        logger.debug(f'{log_prefix}: Mounting ZFS snapshot {full_snapshot_name} at {snapshot_path}{dry_run_label}')

        if not dry_run:
            os.makedirs(snapshot_path, mode=0o700, exist_ok=True)
            borgmatic.execute.execute_command(
                (
                    hook_config.get('mount_command', 'mount'),
                    '-t',
                    'zfs',
                    f'{dataset_name}@{snapshot_name}',
                    snapshot_path,
                ),
                output_log_level=logging.DEBUG,
            )

        if not dry_run:
            source_directories.remove(mount_point)
            source_directories.append(snapshot_path)

    return []


def remove_data_source_dumps(hook_config, config, log_prefix, borgmatic_runtime_directory, dry_run):
    '''
    Given a ZFS configuration dict, a configuration dict, a log prefix, the borgmatic runtime
    directory, and whether this is a dry run, unmount and destroy any ZFS snapshots created by
    borgmatic. Use the log prefix in any log entries. If this is a dry run or ZFS isn't enabled,
    then don't actually remove anything.
    '''
    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    # Unmount snapshots.
    zfs_command = hook_config.get('zfs_command', 'zfs')
    list_datasets_command = (
        zfs_command,
        'list',
        '-H',
        '-o',
        'name,mountpoint',
    )
    try:
        list_datasets_output = borgmatic.execute.execute_command_and_capture_output(
            list_datasets_command
        )
    except FileNotFoundError:
        logger.debug(f'{log_prefix}: Could not find "{zfs_command}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(f'{log_prefix}: {error}')
        return

    mount_points = tuple(
        mount_point
        for line in list_datasets_output.splitlines()
        for (dataset_name, mount_point) in (line.rstrip().split('\t'),)
    )
    # FIXME: This doesn't necessarily find snapshot mounts from previous borgmatic runs, because
    # borgmatic_runtime_directory could be in a tempfile-created directory that has a random name.
    snapshots_directory = os.path.join(
        os.path.normpath(borgmatic_runtime_directory),
        'zfs_snapshots',
    )
    logger.debug(f'{log_prefix}: Looking for snapshots to remove in {snapshots_directory}{dry_run_label}')

    if os.path.isdir(snapshots_directory):
        for mount_point in mount_points:
            snapshot_path = os.path.join(snapshots_directory, mount_point.lstrip(os.path.sep))
            logger.debug(f'{log_prefix}: Unmounting ZFS snapshot at {snapshot_path}{dry_run_label}')

            if not dry_run:
                borgmatic.execute.execute_command(
                    (
                        hook_config.get('umount_command', 'umount'),
                        snapshot_path,
                    ),
                    output_log_level=logging.DEBUG,
                )

    # Destroy snapshots.
    list_snapshots_command = (
        zfs_command,
        'list',
        '-H',
        '-t',
        'snapshot',
        '-o',
        'name',
    )
    list_snapshots_output = borgmatic.execute.execute_command_and_capture_output(
        list_snapshots_command
    )

    for line in list_snapshots_output.splitlines():
        full_snapshot_name = line.rstrip()
        logger.debug(f'{log_prefix}: Destroying ZFS snapshot {full_snapshot_name}{dry_run_label}')

        # Only destroy snapshots that borgmatic actually created!
        if not full_snapshot_name.split('@')[-1].startswith(BORGMATIC_SNAPSHOT_PREFIX):
            continue

        if not dry_run:
            borgmatic.execute.execute_command(
                (
                    zfs_command,
                    'destroy',
                    '-r',
                    full_snapshot_name,
                ),
                output_log_level=logging.DEBUG,
            )


def make_data_source_dump_patterns(hook_config, config, log_prefix, name=None):  # pragma: no cover
    '''
    Restores aren't implemented, because stored files can be extracted directly with "extract".
    '''
    raise NotImplementedError()


def restore_data_source_dump(
    hook_config, config, log_prefix, data_source, dry_run, extract_process, connection_params
):  # pragma: no cover
    '''
    Restores aren't implemented, because stored files can be extracted directly with "extract".
    '''
    raise NotImplementedError()
