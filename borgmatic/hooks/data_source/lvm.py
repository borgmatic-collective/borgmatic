import collections
import glob
import json
import logging
import os
import shutil
import subprocess

import borgmatic.config.paths
import borgmatic.hooks.data_source.snapshot
import borgmatic.execute

logger = logging.getLogger(__name__)


def use_streaming(hook_config, config, log_prefix):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


BORGMATIC_SNAPSHOT_PREFIX = 'borgmatic-'
Logical_volume = collections.namedtuple(
    'Logical_volume', ('name', 'device_path', 'mount_point', 'contained_source_directories')
)


def get_logical_volumes(lsblk_command, source_directories=None):
    '''
    Given an lsblk command to run and a sequence of configured source directories, find the
    intersection between the current LVM logical volume mount points and the configured borgmatic
    source directories. The idea is that these are the requested logical volumes to snapshot.

    If source directories is None, include all logical volume mounts points, not just those in
    source directories.

    Return the result as a sequence of Logical_volume instances.
    '''
    try:
        devices_info = json.loads(
            borgmatic.execute.execute_command_and_capture_output(
                # Use lsblk instead of lvs here because lvs can't show active mounts.
                tuple(lsblk_command.split(' '))
                + (
                    '--output',
                    'name,path,mountpoint,type',
                    '--json',
                    '--list',
                )
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(f'Invalid {lsblk_command} JSON output: {error}')

    candidate_source_directories = set(source_directories or ())

    try:
        return tuple(
            Logical_volume(
                device['name'], device['path'], device['mountpoint'], contained_source_directories
            )
            for device in devices_info['blockdevices']
            if device['mountpoint'] and device['type'] == 'lvm'
            for contained_source_directories in (
                borgmatic.hooks.data_source.snapshot.get_contained_directories(
                    device['mountpoint'], candidate_source_directories
                ),
            )
            if not source_directories or contained_source_directories
        )
    except KeyError as error:
        raise ValueError(f'Invalid {lsblk_command} output: Missing key "{error}"')


def snapshot_logical_volume(
    lvcreate_command,
    snapshot_name,
    logical_volume_device,
    snapshot_size,
):  # pragma: no cover
    '''
    Given an lvcreate command to run, a snapshot name, the path to the logical volume device to
    snapshot, and a snapshot size string, create a new LVM snapshot.
    '''
    borgmatic.execute.execute_command(
        tuple(lvcreate_command.split(' '))
        + (
            '--snapshot',
            ('--extents' if '%' in snapshot_size else '--size'),
            snapshot_size,
            '--name',
            snapshot_name,
            logical_volume_device,
        ),
        output_log_level=logging.DEBUG,
    )


def mount_snapshot(mount_command, snapshot_device, snapshot_mount_path):  # pragma: no cover
    '''
    Given a mount command to run, the device path for an existing snapshot, and the path where the
    snapshot should be mounted, mount the snapshot as read-only (making any necessary directories
    first).
    '''
    os.makedirs(snapshot_mount_path, mode=0o700, exist_ok=True)

    borgmatic.execute.execute_command(
        tuple(mount_command.split(' '))
        + (
            '-o',
            'ro',
            snapshot_device,
            snapshot_mount_path,
        ),
        output_log_level=logging.DEBUG,
    )


DEFAULT_SNAPSHOT_SIZE = '10%ORIGIN'


def dump_data_sources(
    hook_config,
    config,
    log_prefix,
    config_paths,
    borgmatic_runtime_directory,
    source_directories,
    dry_run,
):
    '''
    Given an LVM configuration dict, a configuration dict, a log prefix, the borgmatic configuration
    file paths, the borgmatic runtime directory, the configured source directories, and whether this
    is a dry run, auto-detect and snapshot any LVM logical volume mount points listed in the given
    source directories. Also update those source directories, replacing logical volume mount points
    with corresponding snapshot directories so they get stored in the Borg archive instead. Use the
    log prefix in any log entries.

    Return an empty sequence, since there are no ongoing dump processes from this hook.

    If this is a dry run, then don't actually snapshot anything.
    '''
    dry_run_label = ' (dry run; not actually snapshotting anything)' if dry_run else ''
    logger.info(f'{log_prefix}: Snapshotting LVM logical volumes{dry_run_label}')

    # List logical volumes to get their mount points.
    lsblk_command = hook_config.get('lsblk_command', 'lsblk')
    requested_logical_volumes = get_logical_volumes(lsblk_command, source_directories)

    # Snapshot each logical volume, rewriting source directories to use the snapshot paths.
    snapshot_suffix = f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}'
    normalized_runtime_directory = os.path.normpath(borgmatic_runtime_directory)

    if not requested_logical_volumes:
        logger.warning(f'{log_prefix}: No LVM logical volumes found to snapshot{dry_run_label}')

    for logical_volume in requested_logical_volumes:
        snapshot_name = f'{logical_volume.name}_{snapshot_suffix}'
        logger.debug(
            f'{log_prefix}: Creating LVM snapshot {snapshot_name} of {logical_volume.mount_point}{dry_run_label}'
        )

        if not dry_run:
            snapshot_logical_volume(
                hook_config.get('lvcreate_command', 'lvcreate'),
                snapshot_name,
                logical_volume.device_path,
                hook_config.get('snapshot_size', DEFAULT_SNAPSHOT_SIZE),
            )

        # Get the device path for the snapshot we just created.
        try:
            snapshot = get_snapshots(
                hook_config.get('lvs_command', 'lvs'), snapshot_name=snapshot_name
            )[0]
        except IndexError:
            raise ValueError(f'Cannot find LVM snapshot {snapshot_name}')

        # Mount the snapshot into a particular named temporary directory so that the snapshot ends
        # up in the Borg archive at the "original" logical volume mount point path.
        snapshot_mount_path = os.path.join(
            normalized_runtime_directory,
            'lvm_snapshots',
            logical_volume.mount_point.lstrip(os.path.sep),
        )

        logger.debug(
            f'{log_prefix}: Mounting LVM snapshot {snapshot_name} at {snapshot_mount_path}{dry_run_label}'
        )

        if dry_run:
            continue

        mount_snapshot(
            hook_config.get('mount_command', 'mount'), snapshot.device_path, snapshot_mount_path
        )

        # Update the path for each contained source directory, so Borg sees it within the
        # mounted snapshot.
        for source_directory in logical_volume.contained_source_directories:
            try:
                source_directories.remove(source_directory)
            except ValueError:
                pass

            source_directories.append(
                os.path.join(
                    normalized_runtime_directory,
                    'lvm_snapshots',
                    '.',  # Borg 1.4+ "slashdot" hack.
                    source_directory.lstrip(os.path.sep),
                )
            )

    return []


def unmount_snapshot(umount_command, snapshot_mount_path):  # pragma: no cover
    '''
    Given a umount command to run and the mount path of a snapshot, unmount it.
    '''
    borgmatic.execute.execute_command(
        tuple(umount_command.split(' '))
        + (
            snapshot_mount_path,
        ),
        output_log_level=logging.DEBUG,
    )


def remove_snapshot(lvremove_command, snapshot_device_path):  # pragma: no cover
    '''
    Given an lvremove command to run and the device path of a snapshot, remove it it.
    '''
    borgmatic.execute.execute_command(
        tuple(lvremove_command.split(' '))
        + (
            '--force',  # Suppress an interactive "are you sure?" type prompt.
            snapshot_device_path,
        ),
        output_log_level=logging.DEBUG,
    )


Snapshot = collections.namedtuple(
    'Snapshot',
    ('name', 'device_path'),
)


def get_snapshots(lvs_command, snapshot_name=None):
    '''
    Given an lvs command to run, return all LVM snapshots as a sequence of Snapshot instances.

    If a snapshot name is given, filter the results to that snapshot.
    '''
    try:
        snapshot_info = json.loads(
            borgmatic.execute.execute_command_and_capture_output(
                # Use lvs instead of lsblk here because lsblk can't filter to just snapshots.
                tuple(lvs_command.split(' '))
                + (
                    '--report-format',
                    'json',
                    '--options',
                    'lv_name,lv_path',
                    '--select',
                    'lv_attr =~ ^s',  # Filter to just snapshots.
                )
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(f'Invalid {lvs_command} JSON output: {error}')

    try:
        return tuple(
            Snapshot(snapshot['lv_name'], snapshot['lv_path'])
            for snapshot in snapshot_info['report'][0]['lv']
            if snapshot_name is None or snapshot['lv_name'] == snapshot_name
        )
    except KeyError as error:
        raise ValueError(f'Invalid {lvs_command} output: Missing key "{error}"')


def remove_data_source_dumps(hook_config, config, log_prefix, borgmatic_runtime_directory, dry_run):
    '''
    Given an LVM configuration dict, a configuration dict, a log prefix, the borgmatic runtime
    directory, and whether this is a dry run, unmount and delete any LVM snapshots created by
    borgmatic. Use the log prefix in any log entries. If this is a dry run, then don't actually
    remove anything.
    '''
    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    # Unmount snapshots.
    try:
        logical_volumes = get_logical_volumes(hook_config.get('lsblk_command', 'lsblk'))
    except FileNotFoundError as error:
        logger.debug(f'{log_prefix}: Could not find "{error.filename}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(f'{log_prefix}: {error}')
        return

    snapshots_glob = os.path.join(
        borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(borgmatic_runtime_directory),
        ),
        'lvm_snapshots',
    )
    logger.debug(
        f'{log_prefix}: Looking for snapshots to remove in {snapshots_glob}{dry_run_label}'
    )
    umount_command = hook_config.get('umount_command', 'umount')

    for snapshots_directory in glob.glob(snapshots_glob):
        if not os.path.isdir(snapshots_directory):
            continue

        for logical_volume in logical_volumes:
            snapshot_mount_path = os.path.join(
                snapshots_directory, logical_volume.mount_point.lstrip(os.path.sep)
            )
            if not os.path.isdir(snapshot_mount_path):
                continue

            # This might fail if the directory is already mounted, but we swallow errors here since
            # we'll do another recursive delete below. The point of doing it here is that we don't
            # want to try to unmount a non-mounted directory (which *will* fail).
            if not dry_run:
                shutil.rmtree(snapshot_mount_path, ignore_errors=True)

            # If the delete was successful, that means there's nothing to unmount.
            if not os.path.isdir(snapshot_mount_path):
                continue

            logger.debug(
                f'{log_prefix}: Unmounting LVM snapshot at {snapshot_mount_path}{dry_run_label}'
            )

            if not dry_run:
                try:
                    unmount_snapshot(umount_command, snapshot_mount_path)
                except FileNotFoundError:
                    logger.debug(f'{log_prefix}: Could not find "{umount_command}" command')
                    return
                except subprocess.CalledProcessError as error:
                    logger.debug(f'{log_prefix}: {error}')
                    return

        if not dry_run:
            shutil.rmtree(snapshots_directory)

    # Delete snapshots.
    lvremove_command = hook_config.get('lvremove_command', 'lvremove')

    for snapshot in get_snapshots(hook_config.get('lvs_command', 'lvs')):
        # Only delete snapshots that borgmatic actually created!
        if not snapshot.name.split('_')[-1].startswith(BORGMATIC_SNAPSHOT_PREFIX):
            continue

        logger.debug(f'{log_prefix}: Deleting LVM snapshot {snapshot.name}{dry_run_label}')

        if not dry_run:
            remove_snapshot(lvremove_command, snapshot.device_path)


def make_data_source_dump_patterns(
    hook_config, config, log_prefix, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Restores aren't implemented, because stored files can be extracted directly with "extract".
    '''
    return ()


def restore_data_source_dump(
    hook_config,
    config,
    log_prefix,
    data_source,
    dry_run,
    extract_process,
    connection_params,
    borgmatic_runtime_directory,
):  # pragma: no cover
    '''
    Restores aren't implemented, because stored files can be extracted directly with "extract".
    '''
    raise NotImplementedError()
