import collections
import glob
import itertools
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


def get_contained_subvolume_paths(btrfs_command, subvolume_path):
    '''
    Given the path of a Btrfs subvolume, return it in a sequence along with the paths of its
    contained subvolumes.

    If the btrfs command errors, log that error and return an empty sequence.
    '''
    try:
        btrfs_output = borgmatic.execute.execute_command_and_capture_output(
            tuple(btrfs_command.split(' '))
            + (
                'subvolume',
                'list',
                subvolume_path,
            ),
            close_fds=True,
        )
    except subprocess.CalledProcessError as error:
        logger.debug(
            f'Ignoring Btrfs subvolume {subvolume_path} because of error listing its subvolumes: {error}'
        )

        return ()

    return (subvolume_path,) + tuple(
        os.path.join(subvolume_path, line.split(' ')[-1])
        for line in btrfs_output.splitlines()
        if line.strip()
    )


FINDMNT_BTRFS_ROOT_SUBVOLUME_OPTION = 'subvolid=5'


def get_all_subvolume_paths(btrfs_command, findmnt_command):
    '''
    Given btrfs and findmnt commands to run, get the sorted paths for all Btrfs subvolumes on the
    system.
    '''
    findmnt_output = borgmatic.execute.execute_command_and_capture_output(
        tuple(findmnt_command.split(' '))
        + (
            '-t',  # Filesystem type.
            'btrfs',
            '--json',
            '--list',  # Request a flat list instead of a nested subvolume hierarchy.
        ),
        close_fds=True,
    )

    try:
        return tuple(
            sorted(
                itertools.chain.from_iterable(
                    # If findmnt gave us a Btrfs root filesystem, list the subvolumes within it.
                    # This is necessary because findmnt only returns a subvolume's mount point
                    # rather than its original subvolume path (which can differ). For instance,
                    # a subvolume might exist at /mnt/subvolume but be mounted at /home/myuser.
                    # findmnt is still useful though because it's a global way to discover all
                    # Btrfs subvolumes—even if we have to do some additional legwork ourselves.
                    (
                        get_contained_subvolume_paths(btrfs_command, filesystem['target'])
                        if FINDMNT_BTRFS_ROOT_SUBVOLUME_OPTION in filesystem['options'].split(',')
                        else (filesystem['target'],)
                    )
                    for filesystem in json.loads(findmnt_output)['filesystems']
                )
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError(f'Invalid {findmnt_command} JSON output: {error}')
    except KeyError as error:
        raise ValueError(f'Invalid {findmnt_command} output: Missing key "{error}"')


Subvolume = collections.namedtuple('Subvolume', ('path', 'contained_patterns'), defaults=((),))


def get_subvolume_property(btrfs_command, subvolume_path, property_name):
    '''
    Given a btrfs command, a subvolume path, and a property name to lookup, return the value of the
    corresponding property.

    Raise subprocess.CalledProcessError if the btrfs command errors.
    '''
    output = borgmatic.execute.execute_command_and_capture_output(
        tuple(btrfs_command.split(' '))
        + (
            'property',
            'get',
            '-t',  # Type.
            'subvol',
            subvolume_path,
            property_name,
        ),
        close_fds=True,
    )

    try:
        value = output.strip().split('=')[1]
    except IndexError:
        raise ValueError(f'Invalid {btrfs_command} property output')

    return {
        'true': True,
        'false': False,
    }.get(value, value)


def omit_read_only_subvolume_paths(btrfs_command, subvolume_paths):
    '''
    Given a Btrfs command to run and a sequence of Btrfs subvolume paths, filter them down to just
    those that are read-write. The idea is that Btrfs can't actually snapshot a read-only subvolume,
    so we should just ignore them.
    '''
    retained_subvolume_paths = []

    for subvolume_path in subvolume_paths:
        try:
            if get_subvolume_property(btrfs_command, subvolume_path, 'ro'):
                logger.debug(f'Ignoring Btrfs subvolume {subvolume_path} because it is read-only')
            else:
                retained_subvolume_paths.append(subvolume_path)
        except subprocess.CalledProcessError as error:
            logger.debug(
                f'Error determining read-only status of Btrfs subvolume {subvolume_path}: {error}'
            )

    return tuple(retained_subvolume_paths)


def get_subvolumes(btrfs_command, findmnt_command, patterns=None):
    '''
    Given a Btrfs command to run and a sequence of configured patterns, find the intersection
    between the current Btrfs filesystem and subvolume paths and the paths of any patterns.  The
    idea is that these pattern paths represent the requested subvolumes to snapshot.

    Only include subvolumes that contain at least one root pattern sourced from borgmatic
    configuration (as opposed to generated elsewhere in borgmatic). But if patterns is None, then
    return all subvolumes instead, sorted by path.

    Return the result as a sequence of matching Subvolume instances.
    '''
    candidate_patterns = set(patterns or ())
    subvolumes = []

    # For each subvolume path, match it against the given patterns to find the subvolumes to
    # backup. Sort the subvolumes from longest to shortest mount points, so longer mount points get
    # a whack at the candidate pattern piñata before their parents do. (Patterns are consumed during
    # this process, so no two subvolumes end up with the same contained patterns.)
    for subvolume_path in reversed(
        omit_read_only_subvolume_paths(
            btrfs_command, get_all_subvolume_paths(btrfs_command, findmnt_command)
        )
    ):
        subvolumes.extend(
            Subvolume(subvolume_path, contained_patterns)
            for contained_patterns in (
                borgmatic.hooks.data_source.snapshot.get_contained_patterns(
                    subvolume_path, candidate_patterns
                ),
            )
            if patterns is None
            or any(
                pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
                and pattern.source == borgmatic.borg.pattern.Pattern_source.CONFIG
                for pattern in contained_patterns
            )
        )

    return tuple(sorted(subvolumes, key=lambda subvolume: subvolume.path))


BORGMATIC_SNAPSHOT_PREFIX = '.borgmatic-snapshot-'


def make_snapshot_path(subvolume_path):
    '''
    Given the path to a subvolume, make a corresponding snapshot path for it.
    '''
    return os.path.join(
        subvolume_path,
        f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}',
        # Included so that the snapshot ends up in the Borg archive at the "original" subvolume path.
    ) + subvolume_path.rstrip(os.path.sep)


def make_snapshot_exclude_pattern(subvolume_path):  # pragma: no cover
    '''
    Given the path to a subvolume, make a corresponding exclude pattern for its embedded snapshot
    path. This is to work around a quirk of Btrfs: If you make a snapshot path as a child directory
    of a subvolume, then the snapshot's own initial directory component shows up as an empty
    directory within the snapshot itself. For instance, if you have a Btrfs subvolume at /mnt and
    make a snapshot of it at:

        /mnt/.borgmatic-snapshot-1234/mnt

    ... then the snapshot itself will have an empty directory at:

        /mnt/.borgmatic-snapshot-1234/mnt/.borgmatic-snapshot-1234

    So to prevent that from ending up in the Borg archive, this function produces an exclude pattern
    to exclude that path.
    '''
    snapshot_directory = f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}'

    return borgmatic.borg.pattern.Pattern(
        os.path.join(
            subvolume_path,
            snapshot_directory,
            subvolume_path.lstrip(os.path.sep),
            snapshot_directory,
        ),
        borgmatic.borg.pattern.Pattern_type.NO_RECURSE,
        borgmatic.borg.pattern.Pattern_style.FNMATCH,
        source=borgmatic.borg.pattern.Pattern_source.HOOK,
    )


def make_borg_snapshot_pattern(subvolume_path, pattern):
    '''
    Given the path to a subvolume and a pattern as a borgmatic.borg.pattern.Pattern instance whose
    path is inside the subvolume, return a new Pattern with its path rewritten to be in a snapshot
    path intended for giving to Borg.

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
        subvolume_path,
        f'{BORGMATIC_SNAPSHOT_PREFIX}{os.getpid()}',
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
            '-r',  # Read-only.
            subvolume_path,
            snapshot_path,
        ),
        output_log_level=logging.DEBUG,
        close_fds=True,
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
    Given a Btrfs configuration dict, a configuration dict, the borgmatic configuration file paths,
    the borgmatic runtime directory, the configured patterns, and whether this is a dry run,
    auto-detect and snapshot any Btrfs subvolume paths listed in the given patterns. Also update
    those patterns, replacing subvolume paths with corresponding snapshot directories so they get
    stored in the Borg archive instead.

    Return an empty sequence, since there are no ongoing dump processes from this hook.

    If this is a dry run, then don't actually snapshot anything.
    '''
    dry_run_label = ' (dry run; not actually snapshotting anything)' if dry_run else ''
    logger.info(f'Snapshotting Btrfs subvolumes{dry_run_label}')

    # Based on the configured patterns, determine Btrfs subvolumes to backup. Only consider those
    # patterns that came from actual user configuration (as opposed to, say, other hooks).
    btrfs_command = hook_config.get('btrfs_command', 'btrfs')
    findmnt_command = hook_config.get('findmnt_command', 'findmnt')
    subvolumes = get_subvolumes(btrfs_command, findmnt_command, patterns)

    if not subvolumes:
        logger.warning(f'No Btrfs subvolumes found to snapshot{dry_run_label}')

    # Snapshot each subvolume, rewriting patterns to use their snapshot paths.
    for subvolume in subvolumes:
        logger.debug(f'Creating Btrfs snapshot for {subvolume.path} subvolume')

        snapshot_path = make_snapshot_path(subvolume.path)

        if dry_run:
            continue

        snapshot_subvolume(btrfs_command, subvolume.path, snapshot_path)

        for pattern in subvolume.contained_patterns:
            snapshot_pattern = make_borg_snapshot_pattern(subvolume.path, pattern)

            # Attempt to update the pattern in place, since pattern order matters to Borg.
            try:
                patterns[patterns.index(pattern)] = snapshot_pattern
            except ValueError:
                patterns.append(snapshot_pattern)

        patterns.append(make_snapshot_exclude_pattern(subvolume.path))

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
        close_fds=True,
    )


def remove_data_source_dumps(hook_config, config, borgmatic_runtime_directory, dry_run):
    '''
    Given a Btrfs configuration dict, a configuration dict, the borgmatic runtime directory, and
    whether this is a dry run, delete any Btrfs snapshots created by borgmatic. If this is a dry run
    or Btrfs isn't configured in borgmatic's configuration, then don't actually remove anything.
    '''
    if hook_config is None:
        return

    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    btrfs_command = hook_config.get('btrfs_command', 'btrfs')
    findmnt_command = hook_config.get('findmnt_command', 'findmnt')

    try:
        all_subvolumes = get_subvolumes(btrfs_command, findmnt_command)
    except FileNotFoundError as error:
        logger.debug(f'Could not find "{error.filename}" command')
        return
    except subprocess.CalledProcessError as error:
        logger.debug(error)
        return

    # Reversing the sorted subvolumes ensures that we remove longer paths of child subvolumes before
    # the shorter paths of parent subvolumes.
    for subvolume in reversed(all_subvolumes):
        subvolume_snapshots_glob = borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(make_snapshot_path(subvolume.path)),
            temporary_directory_prefix=BORGMATIC_SNAPSHOT_PREFIX,
        )

        logger.debug(
            f'Looking for snapshots to remove in {subvolume_snapshots_glob}{dry_run_label}'
        )

        for snapshot_path in glob.glob(subvolume_snapshots_glob):
            if not os.path.isdir(snapshot_path):
                continue

            logger.debug(f'Deleting Btrfs snapshot {snapshot_path}{dry_run_label}')

            if dry_run:
                continue

            try:
                delete_snapshot(btrfs_command, snapshot_path)
            except FileNotFoundError:
                logger.debug(f'Could not find "{btrfs_command}" command')
                return
            except subprocess.CalledProcessError as error:
                logger.debug(error)
                return

            # Remove the snapshot parent directory if it still exists. (It might not exist if the
            # snapshot was for "/".)
            snapshot_parent_dir = snapshot_path.rsplit(subvolume.path, 1)[0]

            if os.path.isdir(snapshot_parent_dir):
                shutil.rmtree(snapshot_parent_dir)


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
