import collections
import glob
import logging
import os
import shutil
import subprocess

import borgmatic.config.paths
import borgmatic.execute
import borgmatic.hooks.data_source.snapshot

logger = logging.getLogger(__name__)


def use_streaming(hook_config, config, log_prefix):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


def get_filesystem_mount_points(findmnt_command):
    '''
    Given a findmnt command to run, get all top-level Btrfs filesystem mount points.
    '''
    findmnt_output = borgmatic.execute.execute_command_and_capture_output(
        tuple(findmnt_command.split(' '))
        + (
            '-n',  # No headings.
            '-t',  # Filesystem type.
            'btrfs',
        )
    )

    return tuple(line.rstrip().split(' ')[0] for line in findmnt_output.splitlines())


def get_subvolumes_for_filesystem(btrfs_command, filesystem_mount_point):
    '''
    Given a Btrfs command to run and a Btrfs filesystem mount point, get the sorted subvolumes for
    that filesystem. Include the filesystem itself.
    '''
    btrfs_output = borgmatic.execute.execute_command_and_capture_output(
        tuple(btrfs_command.split(' '))
        + (
            'subvolume',
            'list',
            filesystem_mount_point,
        )
    )

    if not filesystem_mount_point.strip():
        return ()

    return (filesystem_mount_point,) + tuple(
        sorted(
            subvolume_path
            for line in btrfs_output.splitlines()
            for subvolume_subpath in (line.rstrip().split(' ')[-1],)
            for subvolume_path in (os.path.join(filesystem_mount_point, subvolume_subpath),)
            if subvolume_subpath.strip()
        )
    )


Subvolume = collections.namedtuple(
    'Subvolume', ('path', 'contained_source_directories'), defaults=((),)
)


def get_subvolumes(btrfs_command, findmnt_command, source_directories=None):
    '''
    Given a Btrfs command to run and a sequence of configured source directories, find the
    intersection between the current Btrfs filesystem and subvolume mount points and the configured
    borgmatic source directories. The idea is that these are the requested subvolumes to snapshot.

    If the source directories is None, then return all subvolumes, sorted by path.

    Return the result as a sequence of matching subvolume mount points.
    '''
    candidate_source_directories = set(source_directories or ())
    subvolumes = []

    # For each filesystem mount point, find its subvolumes and match them again the given source
    # directories to find the subvolumes to backup. And within this loop, sort the subvolumes from
    # longest to shortest mount points, so longer mount points get a whack at the candidate source
    # directory piñata before their parents do. (Source directories are consumed during this
    # process, so no two datasets get the same contained source directories.)
    for mount_point in get_filesystem_mount_points(findmnt_command):
        subvolumes.extend(
            Subvolume(subvolume_path, contained_source_directories)
            for subvolume_path in reversed(
                get_subvolumes_for_filesystem(btrfs_command, mount_point)
            )
            for contained_source_directories in (
                borgmatic.hooks.data_source.snapshot.get_contained_directories(
                    subvolume_path, candidate_source_directories
                ),
            )
            if source_directories is None or contained_source_directories
        )

    return tuple(sorted(subvolumes, key=lambda subvolume: subvolume.path))


BORGMATIC_SNAPSHOT_PREFIX = '.borgmatic-snapshot-'


def make_snapshot_path(subvolume_path):  # pragma: no cover
    '''
    Given the path to a subvolume, make a corresponding snapshot path for it.
    '''
    return os.path.join(
        subvolume_path,
        f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}',
        # Included so that the snapshot ends up in the Borg archive at the "original" subvolume
        # path.
        subvolume_path.lstrip(os.path.sep),
    )


def make_snapshot_exclude_path(subvolume_path):  # pragma: no cover
    '''
    Given the path to a subvolume, make a corresponding exclude path for its embedded snapshot path.
    This is to work around a quirk of Btrfs: If you make a snapshot path as a child directory of a
    subvolume, then the snapshot's own initial directory component shows up as an empty directory
    within the snapshot itself. For instance, if you have a Btrfs subvolume at /mnt and make a
    snapshot of it at:

        /mnt/.borgmatic-snapshot-1234/mnt

    ... then the snapshot itself will have an empty directory at:

        /mnt/.borgmatic-snapshot-1234/mnt/.borgmatic-snapshot-1234

    So to prevent that from ending up in the Borg archive, this function produces its path for
    exclusion.
    '''
    snapshot_directory = f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}'

    return os.path.join(
        subvolume_path,
        snapshot_directory,
        subvolume_path.lstrip(os.path.sep),
        snapshot_directory,
    )


def make_borg_source_directory_path(subvolume_path, source_directory):  # pragma: no cover
    '''
    Given the path to a subvolume and a source directory inside it, make a corresponding path for
    the source directory within a snapshot path intended for giving to Borg.
    '''
    return os.path.join(
        subvolume_path,
        f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}',
        '.',  # Borg 1.4+ "slashdot" hack.
        # Included so that the source directory ends up in the Borg archive at its "original" path.
        source_directory.lstrip(os.path.sep),
    )


def snapshot_subvolume(btrfs_command, subvolume_path, snapshot_path):  # pragma: no cover
    '''
    Given a Btrfs command to run, the path to a subvolume, and the path for a snapshot, create a new
    Btrfs snapshot of the subvolume.
    '''
    os.makedirs(os.path.dirname(snapshot_path), mode=0o700, exist_ok=True)

    borgmatic.execute.execute_command(
        tuple(btrfs_command.split(' '))
        + (
            'subvolume',
            'snapshot',
            '-r',  # Read-only,
            subvolume_path,
            snapshot_path,
        ),
        output_log_level=logging.DEBUG,
    )


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
    Given a Btrfs configuration dict, a configuration dict, a log prefix, the borgmatic
    configuration file paths, the borgmatic runtime directory, the configured source directories,
    and whether this is a dry run, auto-detect and snapshot any Btrfs subvolume mount points listed
    in the given source directories. Also update those source directories, replacing subvolume mount
    points with corresponding snapshot directories so they get stored in the Borg archive instead.
    Use the log prefix in any log entries.

    Return an empty sequence, since there are no ongoing dump processes from this hook.

    If this is a dry run, then don't actually snapshot anything.
    '''
    dry_run_label = ' (dry run; not actually snapshotting anything)' if dry_run else ''
    logger.info(f'{log_prefix}: Snapshotting Btrfs subvolumes{dry_run_label}')

    # Based on the configured source directories, determine Btrfs subvolumes to backup.
    btrfs_command = hook_config.get('btrfs_command', 'btrfs')
    findmnt_command = hook_config.get('findmnt_command', 'findmnt')
    subvolumes = get_subvolumes(btrfs_command, findmnt_command, source_directories)

    if not subvolumes:
        logger.warning(f'{log_prefix}: No Btrfs subvolumes found to snapshot{dry_run_label}')

    # Snapshot each subvolume, rewriting source directories to use their snapshot paths.
    for subvolume in subvolumes:
        logger.debug(f'{log_prefix}: Creating Btrfs snapshot for {subvolume.path} subvolume')

        snapshot_path = make_snapshot_path(subvolume.path)

        if dry_run:
            continue

        snapshot_subvolume(btrfs_command, subvolume.path, snapshot_path)

        for source_directory in subvolume.contained_source_directories:
            try:
                source_directories.remove(source_directory)
            except ValueError:
                pass

            source_directories.append(
                make_borg_source_directory_path(subvolume.path, source_directory)
            )

        config.setdefault('exclude_patterns', []).append(make_snapshot_exclude_path(subvolume.path))

    return []


def delete_snapshot(btrfs_command, snapshot_path):  # pragma: no cover
    '''
    Given a Btrfs command to run and the name of a snapshot path, delete it.
    '''
    borgmatic.execute.execute_command(
        tuple(btrfs_command.split(' '))
        + (
            'subvolume',
            'delete',
            snapshot_path,
        ),
        output_log_level=logging.DEBUG,
    )


def remove_data_source_dumps(hook_config, config, log_prefix, borgmatic_runtime_directory, dry_run):
    '''
    Given a Btrfs configuration dict, a configuration dict, a log prefix, the borgmatic runtime
    directory, and whether this is a dry run, delete any Btrfs snapshots created by borgmatic. Use
    the log prefix in any log entries. If this is a dry run, then don't actually remove anything.
    '''
    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    btrfs_command = hook_config.get('btrfs_command', 'btrfs')
    findmnt_command = hook_config.get('findmnt_command', 'findmnt')

    try:
        all_subvolumes = get_subvolumes(btrfs_command, findmnt_command)
    except FileNotFoundError as error:
        logger.debug(f'{log_prefix}: Could not find "{error.filename}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(f'{log_prefix}: {error}')
        return

    # Reversing the sorted subvolumes ensures that we remove longer mount point paths of child
    # subvolumes before the shorter mount point paths of parent subvolumes.
    for subvolume in reversed(all_subvolumes):
        subvolume_snapshots_glob = borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(make_snapshot_path(subvolume.path)),
            temporary_directory_prefix=BORGMATIC_SNAPSHOT_PREFIX,
        )

        logger.debug(
            f'{log_prefix}: Looking for snapshots to remove in {subvolume_snapshots_glob}{dry_run_label}'
        )

        for snapshot_path in glob.glob(subvolume_snapshots_glob):
            if not os.path.isdir(snapshot_path):
                continue

            logger.debug(f'{log_prefix}: Deleting Btrfs snapshot {snapshot_path}{dry_run_label}')

            if dry_run:
                continue

            try:
                delete_snapshot(btrfs_command, snapshot_path)
            except FileNotFoundError:
                logger.debug(f'{log_prefix}: Could not find "{btrfs_command}" command')
                return
            except subprocess.CalledProcessError as error:
                logger.debug(f'{log_prefix}: {error}')
                return

            # Strip off the subvolume path from the end of the snapshot path and then delete the
            # resulting directory.
            shutil.rmtree(snapshot_path.rsplit(subvolume.path, 1)[0])


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
