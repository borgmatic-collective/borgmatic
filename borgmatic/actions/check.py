import calendar
import datetime
import hashlib
import itertools
import logging
import os
import pathlib
import random
import shlex
import shutil
import textwrap

import borgmatic.actions.pattern
import borgmatic.borg.check
import borgmatic.borg.create
import borgmatic.borg.environment
import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.repo_list
import borgmatic.borg.state
import borgmatic.config.paths
import borgmatic.config.validate
import borgmatic.execute
import borgmatic.hooks.command

DEFAULT_CHECKS = (
    {'name': 'repository', 'frequency': '1 month'},
    {'name': 'archives', 'frequency': '1 month'},
)


logger = logging.getLogger(__name__)


def parse_checks(config, only_checks=None):
    '''
    Given a configuration dict with a "checks" sequence of dicts and an optional list of override
    checks, return a tuple of named checks to run.

    For example, given a config of:

        {'checks': ({'name': 'repository'}, {'name': 'archives'})}

    This will be returned as:

        ('repository', 'archives')

    If no "checks" option is present in the config, return the DEFAULT_CHECKS. If a checks value
    has a name of "disabled", return an empty tuple, meaning that no checks should be run.
    '''
    checks = only_checks or tuple(
        check_config['name'] for check_config in (config.get('checks', None) or DEFAULT_CHECKS)
    )
    checks = tuple(check.lower() for check in checks)

    if 'disabled' in checks:
        logger.warning(
            'The "disabled" value for the "checks" option is deprecated and will be removed from a future release; use "skip_actions" instead'
        )
        if len(checks) > 1:
            logger.warning(
                'Multiple checks are configured, but one of them is "disabled"; not running any checks'
            )
        return ()

    return checks


def parse_frequency(frequency):
    '''
    Given a frequency string with a number and a unit of time, return a corresponding
    datetime.timedelta instance or None if the frequency is None or "always".

    For instance, given "3 weeks", return datetime.timedelta(weeks=3)

    Raise ValueError if the given frequency cannot be parsed.
    '''
    if not frequency:
        return None

    frequency = frequency.strip().lower()

    if frequency == 'always':
        return None

    try:
        number, time_unit = frequency.split(' ')
        number = int(number)
    except ValueError:
        raise ValueError(f"Could not parse consistency check frequency '{frequency}'")

    if not time_unit.endswith('s'):
        time_unit += 's'

    if time_unit == 'months':
        number *= 30
        time_unit = 'days'
    elif time_unit == 'years':
        number *= 365
        time_unit = 'days'

    try:
        return datetime.timedelta(**{time_unit: number})
    except TypeError:
        raise ValueError(f"Could not parse consistency check frequency '{frequency}'")


WEEKDAY_DAYS = calendar.day_name[0:5]
WEEKEND_DAYS = calendar.day_name[5:7]


def filter_checks_on_frequency(
    config,
    borg_repository_id,
    checks,
    force,
    archives_check_id=None,
    datetime_now=datetime.datetime.now,
):
    '''
    Given a configuration dict with a "checks" sequence of dicts, a Borg repository ID, a sequence
    of checks, whether to force checks to run, and an ID for the archives check potentially being
    run (if any), filter down those checks based on the configured "frequency" for each check as
    compared to its check time file.

    In other words, a check whose check time file's timestamp is too new (based on the configured
    frequency) will get cut from the returned sequence of checks. Example:

    config = {
        'checks': [
            {
                'name': 'archives',
                'frequency': '2 weeks',
            },
        ]
    }

    When this function is called with that config and "archives" in checks, "archives" will get
    filtered out of the returned result if its check time file is newer than 2 weeks old, indicating
    that it's not yet time to run that check again.

    Raise ValueError if a frequency cannot be parsed.
    '''
    if not checks:
        return checks

    filtered_checks = list(checks)

    if force:
        return tuple(filtered_checks)

    for check_config in config.get('checks', DEFAULT_CHECKS):
        check = check_config['name']
        if checks and check not in checks:
            continue

        only_run_on = check_config.get('only_run_on')
        if only_run_on:
            # Use a dict instead of a set to preserve ordering.
            days = dict.fromkeys(only_run_on)

            if 'weekday' in days:
                days = {
                    **dict.fromkeys(day for day in days if day != 'weekday'),
                    **dict.fromkeys(WEEKDAY_DAYS),
                }
            if 'weekend' in days:
                days = {
                    **dict.fromkeys(day for day in days if day != 'weekend'),
                    **dict.fromkeys(WEEKEND_DAYS),
                }

            if calendar.day_name[datetime_now().weekday()] not in days:
                logger.info(
                    f"Skipping {check} check due to day of the week; check only runs on {'/'.join(day.title() for day in days)} (use --force to check anyway)"
                )
                filtered_checks.remove(check)
                continue

        frequency_delta = parse_frequency(check_config.get('frequency'))
        if not frequency_delta:
            continue

        check_time = probe_for_check_time(config, borg_repository_id, check, archives_check_id)
        if not check_time:
            continue

        # If we've not yet reached the time when the frequency dictates we're ready for another
        # check, skip this check.
        if datetime_now() < check_time + frequency_delta:
            remaining = check_time + frequency_delta - datetime_now()
            logger.info(
                f'Skipping {check} check due to configured frequency; {remaining} until next check (use --force to check anyway)'
            )
            filtered_checks.remove(check)

    return tuple(filtered_checks)


def make_archives_check_id(archive_filter_flags):
    '''
    Given a sequence of flags to filter archives, return a unique hash corresponding to those
    particular flags. If there are no flags, return None.
    '''
    if not archive_filter_flags:
        return None

    return hashlib.sha256(' '.join(archive_filter_flags).encode()).hexdigest()


def make_check_time_path(config, borg_repository_id, check_type, archives_check_id=None):
    '''
    Given a configuration dict, a Borg repository ID, the name of a check type ("repository",
    "archives", etc.), and a unique hash of the archives filter flags, return a path for recording
    that check's time (the time of that check last occurring).
    '''
    borgmatic_state_directory = borgmatic.config.paths.get_borgmatic_state_directory(config)

    if check_type in ('archives', 'data'):
        return os.path.join(
            borgmatic_state_directory,
            'checks',
            borg_repository_id,
            check_type,
            archives_check_id if archives_check_id else 'all',
        )

    return os.path.join(
        borgmatic_state_directory,
        'checks',
        borg_repository_id,
        check_type,
    )


def write_check_time(path):  # pragma: no cover
    '''
    Record a check time of now as the modification time of the given path.
    '''
    logger.debug(f'Writing check time at {path}')

    os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
    pathlib.Path(path, mode=0o600).touch()


def read_check_time(path):
    '''
    Return the check time based on the modification time of the given path. Return None if the path
    doesn't exist.
    '''
    logger.debug(f'Reading check time from {path}')

    try:
        return datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    except FileNotFoundError:
        return None


def probe_for_check_time(config, borg_repository_id, check, archives_check_id):
    '''
    Given a configuration dict, a Borg repository ID, the name of a check type ("repository",
    "archives", etc.), and a unique hash of the archives filter flags, return the corresponding
    check time or None if such a check time does not exist.

    When the check type is "archives" or "data", this function probes two different paths to find
    the check time, e.g.:

      ~/.borgmatic/checks/1234567890/archives/9876543210
      ~/.borgmatic/checks/1234567890/archives/all

    ... and returns the maximum modification time of the files found (if any). The first path
    represents a more specific archives check time (a check on a subset of archives), and the second
    is a fallback to the last "all" archives check.

    For other check types, this function reads from a single check time path, e.g.:

      ~/.borgmatic/checks/1234567890/repository
    '''
    check_times = (
        read_check_time(group[0])
        for group in itertools.groupby(
            (
                make_check_time_path(config, borg_repository_id, check, archives_check_id),
                make_check_time_path(config, borg_repository_id, check),
            )
        )
    )

    try:
        return max(check_time for check_time in check_times if check_time)
    except ValueError:
        return None


def upgrade_check_times(config, borg_repository_id):
    '''
    Given a configuration dict and a Borg repository ID, upgrade any corresponding check times on
    disk from old-style paths to new-style paths.

    One upgrade performed is moving the checks directory from:

      {borgmatic_source_directory}/checks (e.g., ~/.borgmatic/checks)

    to:

      {borgmatic_state_directory}/checks (e.g. ~/.local/state/borgmatic)

    Another upgrade is renaming an archive or data check path that looks like:

      {borgmatic_state_directory}/checks/1234567890/archives

    to:

      {borgmatic_state_directory}/checks/1234567890/archives/all
    '''
    borgmatic_source_checks_path = os.path.join(
        borgmatic.config.paths.get_borgmatic_source_directory(config), 'checks'
    )
    borgmatic_state_path = borgmatic.config.paths.get_borgmatic_state_directory(config)
    borgmatic_state_checks_path = os.path.join(borgmatic_state_path, 'checks')

    if os.path.exists(borgmatic_source_checks_path) and not os.path.exists(
        borgmatic_state_checks_path
    ):
        logger.debug(
            f'Upgrading archives check times directory from {borgmatic_source_checks_path} to {borgmatic_state_checks_path}'
        )
        os.makedirs(borgmatic_state_path, mode=0o700, exist_ok=True)
        shutil.move(borgmatic_source_checks_path, borgmatic_state_checks_path)

    for check_type in ('archives', 'data'):
        new_path = make_check_time_path(config, borg_repository_id, check_type, 'all')
        old_path = os.path.dirname(new_path)
        temporary_path = f'{old_path}.temp'

        if not os.path.isfile(old_path) and not os.path.isfile(temporary_path):
            continue

        logger.debug(f'Upgrading archives check time file from {old_path} to {new_path}')

        try:
            shutil.move(old_path, temporary_path)
        except FileNotFoundError:
            pass

        os.mkdir(old_path)
        shutil.move(temporary_path, new_path)


def collect_spot_check_source_paths(
    repository,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    borgmatic_runtime_directory,
):
    '''
    Given a repository configuration dict, a configuration dict, the local Borg version, global
    arguments as an argparse.Namespace instance, the local Borg path, and the remote Borg path,
    collect the source paths that Borg would use in an actual create (but only include files).
    '''
    stream_processes = any(
        borgmatic.hooks.dispatch.call_hooks(
            'use_streaming',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
        ).values()
    )
    working_directory = borgmatic.config.paths.get_working_directory(config)

    (create_flags, create_positional_arguments, pattern_file) = (
        borgmatic.borg.create.make_base_create_command(
            dry_run=True,
            repository_path=repository['path'],
            # Omit "progress" because it interferes with "list_details".
            config=dict(
                {option: value for option, value in config.items() if option != 'progress'},
                list_details=True,
            ),
            patterns=borgmatic.actions.pattern.process_patterns(
                borgmatic.actions.pattern.collect_patterns(config),
                working_directory,
            ),
            local_borg_version=local_borg_version,
            global_arguments=global_arguments,
            borgmatic_runtime_directory=borgmatic_runtime_directory,
            local_path=local_path,
            remote_path=remote_path,
            stream_processes=stream_processes,
        )
    )
    working_directory = borgmatic.config.paths.get_working_directory(config)

    paths_output = borgmatic.execute.execute_command_and_capture_output(
        create_flags + create_positional_arguments,
        capture_stderr=True,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    paths = tuple(
        path_line.split(' ', 1)[1]
        for path_line in paths_output.splitlines()
        if path_line and path_line.startswith('- ') or path_line.startswith('+ ')
    )

    return tuple(
        path for path in paths if os.path.isfile(os.path.join(working_directory or '', path))
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
    (but only include files and symlinks and exclude borgmatic runtime directories).

    These paths do not have a leading slash, as that's how Borg stores them. As a result, we don't
    know whether they came from absolute or relative source directories.
    '''
    borgmatic_source_directory = borgmatic.config.paths.get_borgmatic_source_directory(config)

    return tuple(
        path
        for line in borgmatic.borg.list.capture_archive_listing(
            repository['path'],
            archive,
            config,
            local_borg_version,
            global_arguments,
            path_format='{type} {path}{NUL}',  # noqa: FS003
            local_path=local_path,
            remote_path=remote_path,
        )
        for (file_type, path) in (line.split(' ', 1),)
        if file_type not in (BORG_DIRECTORY_FILE_TYPE, BORG_PIPE_FILE_TYPE)
        if pathlib.Path('borgmatic') not in pathlib.Path(path).parents
        if pathlib.Path(borgmatic_source_directory.lstrip(os.path.sep))
        not in pathlib.Path(path).parents
        if pathlib.Path(borgmatic_runtime_directory.lstrip(os.path.sep))
        not in pathlib.Path(path).parents
    )


SAMPLE_PATHS_SUBSET_COUNT = 5000


def compare_spot_check_hashes(
    repository,
    archive,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    source_paths,
):
    '''
    Given a repository configuration dict, the name of the latest archive, a configuration dict, the
    local Borg version, global arguments as an argparse.Namespace instance, the local Borg path, the
    remote Borg path, and spot check source paths, compare the hashes for a sampling of the source
    paths with hashes from corresponding paths in the given archive. Return a sequence of the paths
    that fail that hash comparison.
    '''
    # Based on the configured sample percentage, come up with a list of random sample files from the
    # source directories.
    spot_check_config = next(check for check in config['checks'] if check['name'] == 'spot')
    sample_count = max(
        int(len(source_paths) * (min(spot_check_config['data_sample_percentage'], 100) / 100)), 1
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
        f'Sampling {sample_count} source paths (~{spot_check_config["data_sample_percentage"]}%) for spot check'
    )

    source_sample_paths_iterator = iter(source_sample_paths)
    source_hashes = {}
    archive_hashes = {}

    # Only hash a few thousand files at a time (a subset of the total paths) to avoid an "Argument
    # list too long" shell error.
    while True:
        # Hash each file in the sample paths (if it exists).
        source_sample_paths_subset = tuple(
            itertools.islice(source_sample_paths_iterator, SAMPLE_PATHS_SUBSET_COUNT)
        )
        if not source_sample_paths_subset:
            break

        hash_output = borgmatic.execute.execute_command_and_capture_output(
            tuple(
                shlex.quote(part)
                for part in shlex.split(spot_check_config.get('xxh64sum_command', 'xxh64sum'))
            )
            + tuple(
                path for path in source_sample_paths_subset if path in hashable_source_sample_path
            ),
            working_directory=working_directory,
        )

        source_hashes.update(
            **dict(
                (reversed(line.split('  ', 1)) for line in hash_output.splitlines()),
                # Represent non-existent files as having empty hashes so the comparison below still
                # works. Same thing for filesystem links, since Borg produces empty archive hashes
                # for them.
                **{
                    path: ''
                    for path in source_sample_paths_subset
                    if path not in hashable_source_sample_path
                },
            )
        )

        # Get the hash for each file in the archive.
        archive_hashes.update(
            **dict(
                reversed(line.split(' ', 1))
                for line in borgmatic.borg.list.capture_archive_listing(
                    repository['path'],
                    archive,
                    config,
                    local_borg_version,
                    global_arguments,
                    list_paths=source_sample_paths_subset,
                    path_format='{xxh64} {path}{NUL}',  # noqa: FS003
                    local_path=local_path,
                    remote_path=remote_path,
                )
                if line
            )
        )

    # Compare the source hashes with the archive hashes to see how many match.
    failing_paths = []

    for path, source_hash in source_hashes.items():
        archive_hash = archive_hashes.get(path.lstrip(os.path.sep))

        if archive_hash is not None and archive_hash == source_hash:
            continue

        failing_paths.append(path)

    return tuple(failing_paths)


MAX_SPOT_CHECK_PATHS_LENGTH = 1000


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
    logger.debug('Running spot check')

    try:
        spot_check_config = next(
            check for check in config.get('checks', ()) if check.get('name') == 'spot'
        )
    except StopIteration:
        raise ValueError('Cannot run spot check because it is unconfigured')

    if spot_check_config['data_tolerance_percentage'] > spot_check_config['data_sample_percentage']:
        raise ValueError(
            'The data_tolerance_percentage must be less than or equal to the data_sample_percentage'
        )

    source_paths = collect_spot_check_source_paths(
        repository,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
        borgmatic_runtime_directory,
    )
    logger.debug(f'{len(source_paths)} total source paths for spot check')

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
            ', '.join(set(archive_paths)) or 'none',
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        logger.debug(f'Paths in latest archive but not source paths: {truncated_archive_paths}')
        raise ValueError(
            'Spot check failed: There are no source paths to compare against the archive'
        )

    # Calculate the percentage delta between the source paths count and the archive paths count, and
    # compare that delta to the configured count tolerance percentage.
    count_delta_percentage = abs(len(source_paths) - len(archive_paths)) / len(source_paths) * 100

    if count_delta_percentage > spot_check_config['count_tolerance_percentage']:
        rootless_source_paths = set(path.lstrip(os.path.sep) for path in source_paths)
        truncated_exclusive_source_paths = textwrap.shorten(
            ', '.join(rootless_source_paths - set(archive_paths)) or 'none',
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        logger.debug(
            f'Paths in source paths but not latest archive: {truncated_exclusive_source_paths}'
        )
        truncated_exclusive_archive_paths = textwrap.shorten(
            ', '.join(set(archive_paths) - rootless_source_paths) or 'none',
            width=MAX_SPOT_CHECK_PATHS_LENGTH,
            placeholder=' ...',
        )
        logger.debug(
            f'Paths in latest archive but not source paths: {truncated_exclusive_archive_paths}'
        )
        raise ValueError(
            f'Spot check failed: {count_delta_percentage:.2f}% file count delta between source paths and latest archive (tolerance is {spot_check_config["count_tolerance_percentage"]}%)'
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
        logger.debug(
            f'Source paths with data not matching the latest archive: {truncated_failing_paths}'
        )
        raise ValueError(
            f'Spot check failed: {failing_percentage:.2f}% of source paths with data not matching the latest archive (tolerance is {data_tolerance_percentage}%)'
        )

    logger.info(
        f'Spot check passed with a {count_delta_percentage:.2f}% file count delta and a {failing_percentage:.2f}% file data delta'
    )


def run_check(
    config_filename,
    repository,
    config,
    local_borg_version,
    check_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "check" action for the given repository.

    Raise ValueError if the Borg repository ID cannot be determined.
    '''
    if check_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, check_arguments.repository
    ):
        return

    logger.info('Running consistency checks')

    repository_id = borgmatic.borg.check.get_repository_id(
        repository['path'],
        config,
        local_borg_version,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
    )
    upgrade_check_times(config, repository_id)
    configured_checks = parse_checks(config, check_arguments.only_checks)
    archive_filter_flags = borgmatic.borg.check.make_archive_filter_flags(
        local_borg_version, config, configured_checks, check_arguments
    )
    archives_check_id = make_archives_check_id(archive_filter_flags)
    checks = filter_checks_on_frequency(
        config,
        repository_id,
        configured_checks,
        check_arguments.force,
        archives_check_id,
    )
    borg_specific_checks = set(checks).intersection({'repository', 'archives', 'data'})

    if borg_specific_checks:
        borgmatic.borg.check.check_archives(
            repository['path'],
            config,
            local_borg_version,
            check_arguments,
            global_arguments,
            borg_specific_checks,
            archive_filter_flags,
            local_path=local_path,
            remote_path=remote_path,
        )
        for check in borg_specific_checks:
            write_check_time(make_check_time_path(config, repository_id, check, archives_check_id))

    if 'extract' in checks:
        borgmatic.borg.extract.extract_last_archive_dry_run(
            config,
            local_borg_version,
            global_arguments,
            repository['path'],
            config.get('lock_wait'),
            local_path,
            remote_path,
        )
        write_check_time(make_check_time_path(config, repository_id, 'extract'))

    if 'spot' in checks:
        with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
            spot_check(
                repository,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                borgmatic_runtime_directory,
            )
        write_check_time(make_check_time_path(config, repository_id, 'spot'))
