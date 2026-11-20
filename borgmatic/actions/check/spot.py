import calendar
import contextlib
import datetime
import hashlib
import itertools
import logging
import os
import pathlib
import random
import shlex
import shutil
import subprocess
import textwrap

import borgmatic.actions.check.paths
import borgmatic.actions.config.bootstrap
import borgmatic.actions.pattern
import borgmatic.borg.check
import borgmatic.borg.create
import borgmatic.borg.environment
import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.pattern
import borgmatic.borg.repo_list
import borgmatic.config.paths
import borgmatic.execute


SAMPLE_PATHS_SUBSET_COUNT = 5000
MAX_SPOT_CHECK_PATHS_LENGTH = 1000


logger = logging.getLogger(__name__)


def collect_spot_check_source_paths(
    repository,
    config,
    patterns,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    borgmatic_runtime_directory,
):
    '''
    Given a repository configuration dict, a configuration dict, processed patterns from the
    configuration, the local Borg version, global arguments as an argparse.Namespace instance, the
    local Borg path, the remote Borg path, and the borgmatic runtime directory, collect the source
    paths that Borg would use in an actual create (but only include files).
    '''
    stream_processes = any(
        borgmatic.hooks.dispatch.call_hooks(
            'use_streaming',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
        ).values(),
    )
    working_directory = borgmatic.config.paths.get_working_directory(config)

    (create_flags, create_positional_arguments, _) = borgmatic.borg.create.make_base_create_command(
        dry_run=True,
        repository_path=repository['path'],
        # Omit "progress" because it interferes with "list_details".
        config=dict(config, progress=False, list_details=True),
        patterns=patterns,
        local_borg_version=local_borg_version,
        global_arguments=global_arguments,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
        local_path=local_path,
        remote_path=remote_path,
        stream_processes=stream_processes,
    )

    path_lines = borgmatic.execute.execute_command_and_capture_output(
        create_flags + create_positional_arguments,
        capture_stderr=True,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    paths = (
        path_line.split(' ', 1)[1]
        for path_line in path_lines
        if path_line and path_line.startswith(('- ', '+ '))
    )

    return tuple(
        # Use dict.fromkeys() to deduplicate file paths, which are present in Borg's dry run output
        # when there are overlapping source patterns. For instance, if both "/foo" and
        # "/foo/file.txt" are in configured patterns, then "/foo/file.txt" will show up in Borg's
        # dry run output twice.
        dict.fromkeys(
            path for path in paths if os.path.isfile(os.path.join(working_directory or '', path))
        )
    )


BORG_DIRECTORY_FILE_TYPE = 'd'
BORG_PIPE_FILE_TYPE = 'p'


def collect_spot_check_archive_paths(
    repository,
    archive,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    borgmatic_runtime_directory,
):
    '''
    Given a repository configuration dict, the name of the latest archive, a configuration dict, the
    local Borg version, global arguments as an argparse.Namespace instance, the local Borg path, the
    remote Borg path, and the borgmatic runtime directory, collect the paths from the given archive
    (but only include files and symlinks and exclude borgmatic runtime directories) and return them
    as a set.

    These paths do not have a leading slash, as that's how Borg stores them. As a result, we don't
    know whether they came from absolute or relative source directories.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return {
        entry['path']
        for entry in borgmatic.borg.list.capture_archive_listing(
            repository['path'],
            archive,
            config,
            local_borg_version,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if entry['type'] not in {BORG_DIRECTORY_FILE_TYPE, BORG_PIPE_FILE_TYPE}
        if pathlib.Path('borgmatic') not in pathlib.Path(entry['path']).parents
        if pathlib.Path(borgmatic_source_directory.lstrip(os.path.sep))
        not in pathlib.Path(entry['path']).parents
        if pathlib.Path(borgmatic_runtime_directory.lstrip(os.path.sep))
        not in pathlib.Path(entry['path']).parents
    }


def compare_spot_check_hashes(
    repository,
    archive,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    source_paths,
    archive_paths,
    source_to_archive_root_paths,
):
    '''
    Given a repository configuration dict, the name of the latest archive, a configuration dict, the
    local Borg version, global arguments as an argparse.Namespace instance, the local Borg path, the
    remote Borg path, a sequence of spot check source paths, a set of Borg archive paths, and a
    sequence of tuples mapping from source root path to archive root path, compare the hashes for a
    sampling of the source paths with hashes from corresponding paths in the given archive. Return a
    sequence of the paths that fail that hash comparison.
    '''
    # Based on the configured sample percentage, come up with a list of random sample files from the
    # source directories.
    spot_check_config = next(check for check in config['checks'] if check['name'] == 'spot')
    sample_count = max(
        int(len(source_paths) * (min(spot_check_config['data_sample_percentage'], 100) / 100)),
        1,
    )
    source_sample_paths = tuple(random.SystemRandom().sample(source_paths, sample_count))
    working_directory = borgmatic.config.paths.get_working_directory(config)
    hashable_source_sample_path = {
        source_path
        for source_path in source_sample_paths
        for full_source_path in (os.path.join(working_directory or '', source_path),)
        if os.path.exists(full_source_path)
        if not os.path.islink(full_source_path)
    }
    logger.debug(
        f'Sampling {sample_count} source paths (~{spot_check_config["data_sample_percentage"]}%) for spot check',
    )

    source_sample_paths_iterator = iter(source_sample_paths)
    source_hashes = {}
    archive_hashes = {}
    hard_link_archive_paths = set()
    source_to_archive_paths = {}

    # Only hash a few thousand files at a time (a subset of the total paths) to avoid an "Argument
    # list too long" shell error.
    while True:
        # Hash each file in the sample paths (if it exists).
        source_sample_paths_subset = tuple(
            itertools.islice(source_sample_paths_iterator, SAMPLE_PATHS_SUBSET_COUNT),
        )

        if not source_sample_paths_subset:
            break

        hash_paths = tuple(
            path for path in source_sample_paths_subset if path in hashable_source_sample_path
        )

        try:
            hash_lines = borgmatic.execute.execute_command_and_capture_output(
                tuple(
                    shlex.quote(part)
                    for part in shlex.split(spot_check_config.get('xxh64sum_command', 'xxh64sum'))
                )
                + hash_paths,
                working_directory=working_directory,
            )
            source_hashes.update(
                **dict(
                    zip(
                        # xxh64sum rewrites/escapes the paths that it returns alongside its hashes, for
                        # instance if they contain special characters. When that happens, they don't
                        # match the original source paths and therefore hash lookups fail. So when
                        # building this lookup dict, use the original unaltered paths we provided as
                        # input to xxh64sum.
                        hash_paths,
                        (
                            # For some reason, xxh64sum prefixes the hash with a backslash if the path
                            # contains a newline. Work around that.
                            line.split('  ', 1)[0].lstrip('\\')
                            for line in hash_lines
                        ),
                        strict=False,
                    ),
                    # Represent non-existent files as having empty hashes so the comparison below still
                    # works. Same thing for filesystem links, since Borg produces empty archive hashes
                    # for them.
                    **{
                        path: ''
                        for path in source_sample_paths_subset
                        if path not in hashable_source_sample_path
                    },
                ),
            )
        except subprocess.CalledProcessError:
            # This can happen if a file we planned to hash gets deleted right before we try to hash
            # it. Falling back to individual file hashing allows us to find and mark just the
            # file(s) with problems instead of failing the whole batch.
            logger.warning(
                'Bulk source path hashing failed for this batch; falling back to individual file hashing'
            )

            for hash_path in hash_paths:
                try:
                    hash_lines = borgmatic.execute.execute_command_and_capture_output(
                        (
                            *(
                                shlex.quote(part)
                                for part in shlex.split(
                                    spot_check_config.get('xxh64sum_command', 'xxh64sum')
                                )
                            ),
                            hash_path,
                        ),
                        working_directory=working_directory,
                    )
                    source_hashes[hash_path] = next(hash_lines).split('  ', 1)[0].lstrip('\\')
                except (subprocess.CalledProcessError, StopIteration):
                    logger.warning(
                        f'Source path hashing failed for {hash_path}; treating as missing'
                    )
                    source_hashes[hash_path] = ''

        source_to_archive_paths.update(
            {
                source_path: borgmatic.actions.check.paths.map_source_path_to_archive_path(
                    source_path, archive_paths, source_to_archive_root_paths
                )
                for source_path in source_sample_paths_subset
            }
        )
        archive_sample_paths_subset = tuple(
            source_to_archive_paths[source_path] for source_path in source_sample_paths_subset
        )

        # Get the hash for each file in the archive.
        for entry in borgmatic.borg.list.capture_archive_listing(
            repository['path'],
            archive,
            config,
            local_borg_version,
            global_arguments,
            list_paths=archive_sample_paths_subset,
            path_format='{xxh64}{path}{linktarget}{target}',
            local_path=local_path,
            remote_path=remote_path,
        ):
            if not entry:
                continue

            # Borg can't get hashes of stored hard links. So if this is a hard link path (and not
            # deemed as the "original" by Borg), then save it off so we can skip hashing of it
            # below.
            if entry.get('linktarget') or entry.get('target'):
                hard_link_archive_paths.add(entry['path'])
                continue

            archive_hashes[entry['path']] = entry['xxh64']

    # Compare the source hashes with the archive hashes to see how many match.
    failing_paths = []

    for source_path, source_hash in source_hashes.items():
        archive_path = source_to_archive_paths[source_path]

        if archive_path in hard_link_archive_paths:
            continue

        archive_hash = archive_hashes.get(archive_path)

        if archive_hash is not None and archive_hash == source_hash:
            continue

        failing_paths.append(source_path)

    return tuple(failing_paths)


def spot_check(
    repository,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    borgmatic_runtime_directory,
):
    '''
    Given a repository dict, a loaded configuration dict, the local Borg version, global arguments
    as an argparse.Namespace instance, the local Borg path, the remote Borg path, and the borgmatic
    runtime directory, perform a spot check for the latest archive in the given repository.

    A spot check compares file counts and also the hashes for a random sampling of source files on
    disk to those stored in the latest archive. If any differences are beyond configured tolerances,
    then the check fails.
    '''
    try:
        spot_check_config = next(
            check for check in config.get('checks', ()) if check.get('name') == 'spot'
        )
    except StopIteration:
        raise ValueError('Cannot run spot check because it is unconfigured')

    if spot_check_config['data_tolerance_percentage'] > spot_check_config['data_sample_percentage']:
        raise ValueError(
            'The data_tolerance_percentage must be less than or equal to the data_sample_percentage',
        )

    archive = borgmatic.borg.repo_list.resolve_archive_name(
        repository['path'],
        'latest',
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
    )
    logger.debug(f'Using archive {archive} for spot check')

    patterns = borgmatic.actions.check.paths.collect_and_process_patterns(
        repository,
        archive,
        config,
        local_borg_version,
        global_arguments,
        borgmatic_runtime_directory,
    )
    source_paths = collect_spot_check_source_paths(
        repository,
        config,
        patterns,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
        borgmatic_runtime_directory,
    )
    logger.debug(f'{len(source_paths)} total source paths for spot check')

    archive_paths = collect_spot_check_archive_paths(
        repository,
        archive,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
        borgmatic_runtime_directory,
    )
    logger.debug(f'{len(archive_paths)} total archive paths for spot check')

    if len(source_paths) == 0:
        truncated_archive_paths = textwrap.shorten(
            ', '.join(sorted(archive_paths)) or 'none',
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        logger.debug(f'Paths in latest archive but not source paths: {truncated_archive_paths}')
        raise ValueError(
            'Spot check failed; there are no source paths to compare against the archive',
        )

    source_to_archive_root_paths = borgmatic.actions.check.paths.make_source_to_archive_root_map(patterns)

    # Calculate the percentage delta between the source paths count and the archive paths count, and
    # compare that delta to the configured count tolerance percentage.
    count_delta_percentage = abs(len(source_paths) - len(archive_paths)) / len(source_paths) * 100

    if count_delta_percentage > spot_check_config['count_tolerance_percentage']:
        source_to_archive_paths = {
            source_path: borgmatic.actions.check.paths.map_source_path_to_archive_path(
                source_path, archive_paths, source_to_archive_root_paths
            )
            for source_path in source_paths
        }
        exclusive_source_paths = tuple(
            source_path
            for source_path, archive_path in source_to_archive_paths.items()
            if archive_path not in archive_paths
        )
        truncated_exclusive_source_paths = textwrap.shorten(
            ', '.join(exclusive_source_paths) or 'none',
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        mapped_archive_paths = set(source_to_archive_paths.values())
        exclusive_archive_paths = sorted(
            archive_path
            for archive_path in archive_paths
            if archive_path not in mapped_archive_paths
        )
        truncated_exclusive_archive_paths = textwrap.shorten(
            ', '.join(exclusive_archive_paths) or 'none',
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        raise ValueError(
            f'Spot check failed\n{count_delta_percentage:.2f}% file count delta between source paths ({len(source_paths)} total) and latest archive ({len(archive_paths)} total); tolerance is {spot_check_config["count_tolerance_percentage"]}%\nOnly in source paths: {truncated_exclusive_source_paths}\nOnly in latest archive: {truncated_exclusive_archive_paths}',
        )

    failing_paths = compare_spot_check_hashes(
        repository,
        archive,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
        source_paths,
        archive_paths,
        source_to_archive_root_paths,
    )

    # Error if the percentage of failing hashes exceeds the configured tolerance percentage.
    logger.debug(f'{len(failing_paths)} non-matching spot check hashes')
    data_tolerance_percentage = spot_check_config['data_tolerance_percentage']
    failing_percentage = (len(failing_paths) / len(source_paths)) * 100

    if failing_percentage > data_tolerance_percentage:
        truncated_failing_paths = textwrap.shorten(
            ', '.join(failing_paths),
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        raise ValueError(
            f'Spot check failed\n{failing_percentage:.2f}% of source paths ({len(failing_paths)} out of {len(source_paths)} checked) with data not matching the latest archive; tolerance is {data_tolerance_percentage}%\nSource paths with non-matching data: {truncated_failing_paths}',
        )

    logger.info(
        f'Spot check passed with a {count_delta_percentage:.2f}% file count delta and a {failing_percentage:.2f}% file data delta',
    )
