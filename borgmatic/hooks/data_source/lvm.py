import collections
import glob
import hashlib
import json
import logging
import os
import shutil
import subprocess

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.execute
import borgmatic.hooks.data_source.snapshot

logger = logging.getLogger(__name__)


def use_streaming(hook_config, config):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


BORGMATIC_SNAPSHOT_PREFIX = 'borgmatic-'
Logical_volume = collections.namedtuple(
    'Logical_volume', ('name', 'device_path', 'mount_point', 'contained_patterns')
)


def get_logical_volumes(lsblk_command, patterns=None):
    '''
    Given an lsblk command to run and a sequence of configured patterns, find the intersection
    between the current LVM logical volume mount points and the paths of any patterns. The idea is
    that these pattern paths represent the requested logical volumes to snapshot.

    Only include logical volumes that contain at least one root pattern sourced from borgmatic
    configuration (as opposed to generated elsewhere in borgmatic). But if patterns is None, include
    all logical volume mounts points instead, not just those in patterns.

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
                ),
                close_fds=True,
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(f'Invalid {lsblk_command} JSON output: {error}')

    candidate_patterns = set(patterns or ())

    try:
        # Sort from longest to shortest mount points, so longer mount points get a whack at the
        # candidate pattern piñata before their parents do. (Patterns are consumed below, so no two
        # logical volumes end up with the same contained patterns.)
        return tuple(
            Logical_volume(device['name'], device['path'], device['mountpoint'], contained_patterns)
            for device in sorted(
                devices_info['blockdevices'],
                key=lambda device: device['mountpoint'] or '',
                reverse=True,
            )
            if device['mountpoint'] and device['type'] == 'lvm'
            for contained_patterns in (
                borgmatic.hooks.data_source.snapshot.get_contained_patterns(
                    device['mountpoint'], candidate_patterns
                ),
            )
            if not patterns
            or any(
                pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
                and pattern.source == borgmatic.borg.pattern.Pattern_source.CONFIG
                for pattern in contained_patterns
            )
        )
    except KeyError as error:
        raise ValueError(f'Invalid {lsblk_command} output: Missing key "{error}"')


def snapshot_logical_volume(
    lvcreate_command,
    snapshot_name,
    logical_volume_device,
    snapshot_size,
):
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
            '--permission',
            'r',  # Read-only.
            '--name',
            snapshot_name,
            logical_volume_device,
        ),
        output_log_level=logging.DEBUG,
        close_fds=True,
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
        close_fds=True,
    )


MOUNT_POINT_HASH_LENGTH = 10


def make_borg_snapshot_pattern(pattern, logical_volume, normalized_runtime_directory):
    '''
    Given a Borg pattern as a borgmatic.borg.pattern.Pattern instance and a Logical_volume
    containing it, return a new Pattern with its path rewritten to be in a snapshot directory based
    on both the given runtime directory and the given Logical_volume's mount point.

    Move any initial caret in a regular expression pattern path to the beginning, so as not to break
    the regular expression.
    '''
    initial_caret = (
        '^'
        if pattern.style == borgmatic.borg.pattern.Pattern_style.REGULAR_EXPRESSION
        and pattern.path.startswith('^')
        else ''
    )

    rewritten_path = initial_caret + os.path.join(
        normalized_runtime_directory,
        'lvm_snapshots',
        # Including this hash prevents conflicts between snapshot patterns for different logical
        # volumes. For instance, without this, snapshotting a logical volume at /var and another at
        # /var/spool would result in overlapping snapshot patterns and therefore colliding mount
        # attempts.
        hashlib.shake_256(logical_volume.mount_point.encode('utf-8')).hexdigest(
            MOUNT_POINT_HASH_LENGTH
        ),
        '.',  # Borg 1.4+ "slashdot" hack.
        # Included so that the source directory ends up in the Borg archive at its "original" path.
        pattern.path.lstrip('^').lstrip(os.path.sep),
    )

    return borgmatic.borg.pattern.Pattern(
        rewritten_path,
        pattern.type,
        pattern.style,
        pattern.device,
        source=borgmatic.borg.pattern.Pattern_source.HOOK,
    )


DEFAULT_SNAPSHOT_SIZE = '10%ORIGIN'


def dump_data_sources(
    hook_config,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Given an LVM configuration dict, a configuration dict, the borgmatic configuration file paths,
    the borgmatic runtime directory, the configured patterns, and whether this is a dry run,
    auto-detect and snapshot any LVM logical volume mount points listed in the given patterns. Also
    update those patterns, replacing logical volume mount points with corresponding snapshot
    directories so they get stored in the Borg archive instead.

    Return an empty sequence, since there are no ongoing dump processes from this hook.

    If this is a dry run, then don't actually snapshot anything.
    '''
    dry_run_label = ' (dry run; not actually snapshotting anything)' if dry_run else ''
    logger.info(f'Snapshotting LVM logical volumes{dry_run_label}')

    # List logical volumes to get their mount points, but only consider those patterns that came
    # from actual user configuration (as opposed to, say, other hooks).
    lsblk_command = hook_config.get('lsblk_command', 'lsblk')
    requested_logical_volumes = get_logical_volumes(lsblk_command, patterns)

    # Snapshot each logical volume, rewriting source directories to use the snapshot paths.
    snapshot_suffix = f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}'
    normalized_runtime_directory = os.path.normpath(borgmatic_runtime_directory)

    if not requested_logical_volumes:
        logger.warning(f'No LVM logical volumes found to snapshot{dry_run_label}')

    for logical_volume in requested_logical_volumes:
        snapshot_name = f'{logical_volume.name}_{snapshot_suffix}'
        logger.debug(
            f'Creating LVM snapshot {snapshot_name} of {logical_volume.mount_point}{dry_run_label}'
        )

        if not dry_run:
            snapshot_logical_volume(
                hook_config.get('lvcreate_command', 'lvcreate'),
                snapshot_name,
                logical_volume.device_path,
                hook_config.get('snapshot_size', DEFAULT_SNAPSHOT_SIZE),
            )

        # Get the device path for the snapshot we just created.
        if not dry_run:
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
            hashlib.shake_256(logical_volume.mount_point.encode('utf-8')).hexdigest(
                MOUNT_POINT_HASH_LENGTH
            ),
            logical_volume.mount_point.lstrip(os.path.sep),
        )

        logger.debug(
            f'Mounting LVM snapshot {snapshot_name} at {snapshot_mount_path}{dry_run_label}'
        )

        if dry_run:
            continue

        mount_snapshot(
            hook_config.get('mount_command', 'mount'), snapshot.device_path, snapshot_mount_path
        )

        for pattern in logical_volume.contained_patterns:
            snapshot_pattern = make_borg_snapshot_pattern(
                pattern, logical_volume, normalized_runtime_directory
            )

            # Attempt to update the pattern in place, since pattern order matters to Borg.
            try:
                patterns[patterns.index(pattern)] = snapshot_pattern
            except ValueError:
                patterns.append(snapshot_pattern)

    return []


def unmount_snapshot(umount_command, snapshot_mount_path):  # pragma: no cover
    '''
    Given a umount command to run and the mount path of a snapshot, unmount it.
    '''
    borgmatic.execute.execute_command(
        tuple(umount_command.split(' ')) + (snapshot_mount_path,),
        output_log_level=logging.DEBUG,
        close_fds=True,
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
        close_fds=True,
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
                ),
                close_fds=True,
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
    except IndexError:
        raise ValueError(f'Invalid {lvs_command} output: Missing report data')
    except KeyError as error:
        raise ValueError(f'Invalid {lvs_command} output: Missing key "{error}"')


def remove_data_source_dumps(hook_config, config, borgmatic_runtime_directory, dry_run):
    '''
    Given an LVM configuration dict, a configuration dict, the borgmatic runtime directory, and
    whether this is a dry run, unmount and delete any LVM snapshots created by borgmatic. If this is
    a dry run or LVM isn't configured in borgmatic's configuration, then don't actually remove
    anything.
    '''
    if hook_config is None:
        return

    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    # Unmount snapshots.
    try:
        logical_volumes = get_logical_volumes(hook_config.get('lsblk_command', 'lsblk'))
    except FileNotFoundError as error:
        logger.debug(f'Could not find "{error.filename}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(error)
        return

    snapshots_glob = os.path.join(
        borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(borgmatic_runtime_directory),
        ),
        'lvm_snapshots',
        '*',
    )
    logger.debug(f'Looking for snapshots to remove in {snapshots_glob}{dry_run_label}')
    umount_command = hook_config.get('umount_command', 'umount')

    for snapshots_directory in glob.glob(snapshots_glob):
        if not os.path.isdir(snapshots_directory):
            continue

        for logical_volume in logical_volumes:
            snapshot_mount_path = os.path.join(
                snapshots_directory, logical_volume.mount_point.lstrip(os.path.sep)
            )

            # If the snapshot mount path is empty, this is probably just a "shadow" of a nested
            # logical volume and therefore there's nothing to unmount.
            if not os.path.isdir(snapshot_mount_path) or not os.listdir(snapshot_mount_path):
                continue

            # This might fail if the directory is already mounted, but we swallow errors here since
            # we'll do another recursive delete below. The point of doing it here is that we don't
            # want to try to unmount a non-mounted directory (which *will* fail).
            if not dry_run:
                shutil.rmtree(snapshot_mount_path, ignore_errors=True)

                # If the delete was successful, that means there's nothing to unmount.
                if not os.path.isdir(snapshot_mount_path):
                    continue

            logger.debug(f'Unmounting LVM snapshot at {snapshot_mount_path}{dry_run_label}')

            if dry_run:
                continue

            try:
                unmount_snapshot(umount_command, snapshot_mount_path)
            except FileNotFoundError:
                logger.debug(f'Could not find "{umount_command}" command')
                return
            except subprocess.CalledProcessError as error:
                logger.debug(error)
                continue

        if not dry_run:
            shutil.rmtree(snapshots_directory, ignore_errors=True)

    # Delete snapshots.
    lvremove_command = hook_config.get('lvremove_command', 'lvremove')

    try:
        snapshots = get_snapshots(hook_config.get('lvs_command', 'lvs'))
    except FileNotFoundError as error:
        logger.debug(f'Could not find "{error.filename}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(error)
        return

    for snapshot in snapshots:
        # Only delete snapshots that borgmatic actually created!
        if not snapshot.name.split('_')[-1].startswith(BORGMATIC_SNAPSHOT_PREFIX):
            continue

        logger.debug(f'Deleting LVM snapshot {snapshot.name}{dry_run_label}')

        if not dry_run:
            remove_snapshot(lvremove_command, snapshot.device_path)


def make_data_source_dump_patterns(
    hook_config, config, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Restores aren't implemented, because stored files can be extracted directly with "extract".
    '''
    return ()


def restore_data_source_dump(
    hook_config,
    config,
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
