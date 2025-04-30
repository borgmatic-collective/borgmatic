import collections
import glob
import hashlib
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
BORGMATIC_USER_PROPERTY = 'org.torsion.borgmatic:backup'


Dataset = collections.namedtuple(
    'Dataset',
    ('name', 'mount_point', 'auto_backup', 'contained_patterns'),
    defaults=(False, ()),
)


def get_datasets_to_backup(zfs_command, patterns):
    '''
    Given a ZFS command to run and a sequence of configured patterns, find the intersection between
    the current ZFS dataset mount points and the paths of any patterns. The idea is that these
    pattern paths represent the requested datasets to snapshot. But also include any datasets tagged
    with a borgmatic-specific user property, whether or not they appear in the patterns.

    Only include datasets that contain at least one root pattern sourced from borgmatic
    configuration (as opposed to generated elsewhere in borgmatic).

    Return the result as a sequence of Dataset instances, sorted by mount point.
    '''
    list_output = borgmatic.execute.execute_command_and_capture_output(
        tuple(zfs_command.split(' '))
        + (
            'list',
            '-H',
            '-t',
            'filesystem',
            '-o',
            f'name,mountpoint,canmount,{BORGMATIC_USER_PROPERTY}',
        ),
        close_fds=True,
    )

    try:
        # Sort from longest to shortest mount points, so longer mount points get a whack at the
        # candidate pattern piñata before their parents do. (Patterns are consumed during the second
        # loop below, so no two datasets end up with the same contained patterns.)
        datasets = sorted(
            (
                Dataset(dataset_name, mount_point, (user_property_value == 'auto'), ())
                for line in list_output.splitlines()
                for (dataset_name, mount_point, can_mount, user_property_value) in (
                    line.rstrip().split('\t'),
                )
                # Skip datasets that are marked "canmount=off", because mounting their snapshots will
                # result in completely empty mount points—thereby preventing us from backing them up.
                if can_mount == 'on'
            ),
            key=lambda dataset: dataset.mount_point,
            reverse=True,
        )
    except ValueError:
        raise ValueError(f'Invalid {zfs_command} list output')

    candidate_patterns = set(patterns)

    return tuple(
        sorted(
            (
                Dataset(
                    dataset.name,
                    dataset.mount_point,
                    dataset.auto_backup,
                    contained_patterns,
                )
                for dataset in datasets
                for contained_patterns in (
                    (
                        (
                            (
                                borgmatic.borg.pattern.Pattern(
                                    dataset.mount_point,
                                    source=borgmatic.borg.pattern.Pattern_source.HOOK,
                                ),
                            )
                            if dataset.auto_backup
                            else ()
                        )
                        + borgmatic.hooks.data_source.snapshot.get_contained_patterns(
                            dataset.mount_point, candidate_patterns
                        )
                    ),
                )
                if dataset.auto_backup
                or any(
                    pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
                    and pattern.source == borgmatic.borg.pattern.Pattern_source.CONFIG
                    for pattern in contained_patterns
                )
            ),
            key=lambda dataset: dataset.mount_point,
        )
    )


def get_all_dataset_mount_points(zfs_command):
    '''
    Given a ZFS command to run, return all ZFS datasets as a sequence of sorted mount points.
    '''
    list_output = borgmatic.execute.execute_command_and_capture_output(
        tuple(zfs_command.split(' '))
        + (
            'list',
            '-H',
            '-t',
            'filesystem',
            '-o',
            'mountpoint',
        ),
        close_fds=True,
    )

    return tuple(
        sorted(
            {
                mount_point
                for line in list_output.splitlines()
                for mount_point in (line.rstrip(),)
                if mount_point != 'none'
            }
        )
    )


def snapshot_dataset(zfs_command, full_snapshot_name):  # pragma: no cover
    '''
    Given a ZFS command to run and a snapshot name of the form "dataset@snapshot", create a new ZFS
    snapshot.
    '''
    borgmatic.execute.execute_command(
        tuple(zfs_command.split(' '))
        + (
            'snapshot',
            full_snapshot_name,
        ),
        output_log_level=logging.DEBUG,
        close_fds=True,
    )


def mount_snapshot(mount_command, full_snapshot_name, snapshot_mount_path):  # pragma: no cover
    '''
    Given a mount command to run, an existing snapshot name of the form "dataset@snapshot", and the
    path where the snapshot should be mounted, mount the snapshot (making any necessary directories
    first).
    '''
    os.makedirs(snapshot_mount_path, mode=0o700, exist_ok=True)

    borgmatic.execute.execute_command(
        tuple(mount_command.split(' '))
        + (
            '-t',
            'zfs',
            '-o',
            'ro',
            full_snapshot_name,
            snapshot_mount_path,
        ),
        output_log_level=logging.DEBUG,
        close_fds=True,
    )


MOUNT_POINT_HASH_LENGTH = 10


def make_borg_snapshot_pattern(pattern, dataset, normalized_runtime_directory):
    '''
    Given a Borg pattern as a borgmatic.borg.pattern.Pattern instance and the Dataset containing it,
    return a new Pattern with its path rewritten to be in a snapshot directory based on both the
    given runtime directory and the given Dataset's mount point.

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
        'zfs_snapshots',
        # Including this hash prevents conflicts between snapshot patterns for different datasets.
        # For instance, without this, snapshotting a dataset at /var and another at /var/spool would
        # result in overlapping snapshot patterns and therefore colliding mount attempts.
        hashlib.shake_256(dataset.mount_point.encode('utf-8')).hexdigest(MOUNT_POINT_HASH_LENGTH),
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


def dump_data_sources(
    hook_config,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Given a ZFS configuration dict, a configuration dict, the borgmatic configuration file paths,
    the borgmatic runtime directory, the configured patterns, and whether this is a dry run,
    auto-detect and snapshot any ZFS dataset mount points listed in the given patterns and any
    dataset with a borgmatic-specific user property. Also update those patterns, replacing dataset
    mount points with corresponding snapshot directories so they get stored in the Borg archive
    instead.

    Return an empty sequence, since there are no ongoing dump processes from this hook.

    If this is a dry run, then don't actually snapshot anything.
    '''
    dry_run_label = ' (dry run; not actually snapshotting anything)' if dry_run else ''
    logger.info(f'Snapshotting ZFS datasets{dry_run_label}')

    # List ZFS datasets to get their mount points, but only consider those patterns that came from
    # actual user configuration (as opposed to, say, other hooks).
    zfs_command = hook_config.get('zfs_command', 'zfs')
    requested_datasets = get_datasets_to_backup(zfs_command, patterns)

    # Snapshot each dataset, rewriting patterns to use the snapshot paths.
    snapshot_name = f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}'
    normalized_runtime_directory = os.path.normpath(borgmatic_runtime_directory)

    if not requested_datasets:
        logger.warning(f'No ZFS datasets found to snapshot{dry_run_label}')

    for dataset in requested_datasets:
        full_snapshot_name = f'{dataset.name}@{snapshot_name}'
        logger.debug(
            f'Creating ZFS snapshot {full_snapshot_name} of {dataset.mount_point}{dry_run_label}'
        )

        if not dry_run:
            snapshot_dataset(zfs_command, full_snapshot_name)

        # Mount the snapshot into a particular named temporary directory so that the snapshot ends
        # up in the Borg archive at the "original" dataset mount point path.
        snapshot_mount_path = os.path.join(
            normalized_runtime_directory,
            'zfs_snapshots',
            hashlib.shake_256(dataset.mount_point.encode('utf-8')).hexdigest(
                MOUNT_POINT_HASH_LENGTH
            ),
            dataset.mount_point.lstrip(os.path.sep),
        )

        logger.debug(
            f'Mounting ZFS snapshot {full_snapshot_name} at {snapshot_mount_path}{dry_run_label}'
        )

        if dry_run:
            continue

        mount_snapshot(
            hook_config.get('mount_command', 'mount'), full_snapshot_name, snapshot_mount_path
        )

        for pattern in dataset.contained_patterns:
            snapshot_pattern = make_borg_snapshot_pattern(
                pattern, dataset, normalized_runtime_directory
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


def destroy_snapshot(zfs_command, full_snapshot_name):  # pragma: no cover
    '''
    Given a ZFS command to run and the name of a snapshot in the form "dataset@snapshot", destroy
    it.
    '''
    borgmatic.execute.execute_command(
        tuple(zfs_command.split(' '))
        + (
            'destroy',
            full_snapshot_name,
        ),
        output_log_level=logging.DEBUG,
        close_fds=True,
    )


def get_all_snapshots(zfs_command):
    '''
    Given a ZFS command to run, return all ZFS snapshots as a sequence of full snapshot names of the
    form "dataset@snapshot".
    '''
    list_output = borgmatic.execute.execute_command_and_capture_output(
        tuple(zfs_command.split(' '))
        + (
            'list',
            '-H',
            '-t',
            'snapshot',
            '-o',
            'name',
        ),
        close_fds=True,
    )

    return tuple(line.rstrip() for line in list_output.splitlines())


def remove_data_source_dumps(hook_config, config, borgmatic_runtime_directory, dry_run):
    '''
    Given a ZFS configuration dict, a configuration dict, the borgmatic runtime directory, and
    whether this is a dry run, unmount and destroy any ZFS snapshots created by borgmatic. If this
    is a dry run or ZFS isn't configured in borgmatic's configuration, then don't actually remove
    anything.
    '''
    if hook_config is None:
        return

    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    # Unmount snapshots.
    zfs_command = hook_config.get('zfs_command', 'zfs')

    try:
        dataset_mount_points = get_all_dataset_mount_points(zfs_command)
    except FileNotFoundError:
        logger.debug(f'Could not find "{zfs_command}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(error)
        return

    snapshots_glob = os.path.join(
        borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(borgmatic_runtime_directory),
        ),
        'zfs_snapshots',
        '*',
    )
    logger.debug(f'Looking for snapshots to remove in {snapshots_glob}{dry_run_label}')
    umount_command = hook_config.get('umount_command', 'umount')

    for snapshots_directory in glob.glob(snapshots_glob):
        if not os.path.isdir(snapshots_directory):
            continue

        # Reversing the sorted datasets ensures that we unmount the longer mount point paths of
        # child datasets before the shorter mount point paths of parent datasets.
        for mount_point in reversed(dataset_mount_points):
            snapshot_mount_path = os.path.join(snapshots_directory, mount_point.lstrip(os.path.sep))

            # If the snapshot mount path is empty, this is probably just a "shadow" of a nested
            # dataset and therefore there's nothing to unmount.
            if not os.path.isdir(snapshot_mount_path) or not os.listdir(snapshot_mount_path):
                continue

            # This might fail if the path is already mounted, but we swallow errors here since we'll
            # do another recursive delete below. The point of doing it here is that we don't want to
            # try to unmount a non-mounted directory (which *will* fail), and probing for whether a
            # directory is mounted is tough to do in a cross-platform way.
            if not dry_run:
                shutil.rmtree(snapshot_mount_path, ignore_errors=True)

                # If the delete was successful, that means there's nothing to unmount.
                if not os.path.isdir(snapshot_mount_path):
                    continue

            logger.debug(f'Unmounting ZFS snapshot at {snapshot_mount_path}{dry_run_label}')

            if not dry_run:
                try:
                    unmount_snapshot(umount_command, snapshot_mount_path)
                except FileNotFoundError:
                    logger.debug(f'Could not find "{umount_command}" command')
                    return
                except subprocess.CalledProcessError as error:
                    logger.debug(error)
                    continue

        if not dry_run:
            shutil.rmtree(snapshot_mount_path, ignore_errors=True)

    # Destroy snapshots.
    full_snapshot_names = get_all_snapshots(zfs_command)

    for full_snapshot_name in full_snapshot_names:
        # Only destroy snapshots that borgmatic actually created!
        if not full_snapshot_name.split('@')[-1].startswith(BORGMATIC_SNAPSHOT_PREFIX):
            continue

        logger.debug(f'Destroying ZFS snapshot {full_snapshot_name}{dry_run_label}')

        if not dry_run:
            destroy_snapshot(zfs_command, full_snapshot_name)


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
