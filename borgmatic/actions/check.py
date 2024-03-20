import datetime
import hashlib
import itertools
import logging
import pathlib
import os

import borgmatic.borg.extract
import borgmatic.borg.check
import borgmatic.borg.state
import borgmatic.config.validate
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


def filter_checks_on_frequency(
    config,
    borg_repository_id,
    checks,
    force,
    archives_check_id=None,
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

        frequency_delta = parse_frequency(check_config.get('frequency'))
        if not frequency_delta:
            continue

        check_time = probe_for_check_time(config, borg_repository_id, check, archives_check_id)
        if not check_time:
            continue

        # If we've not yet reached the time when the frequency dictates we're ready for another
        # check, skip this check.
        if datetime.datetime.now() < check_time + frequency_delta:
            remaining = check_time + frequency_delta - datetime.datetime.now()
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
    borgmatic_source_directory = os.path.expanduser(
        config.get('borgmatic_source_directory', borgmatic.borg.state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY)
    )

    if check_type in ('archives', 'data'):
        return os.path.join(
            borgmatic_source_directory,
            'checks',
            borg_repository_id,
            check_type,
            archives_check_id if archives_check_id else 'all',
        )

    return os.path.join(
        borgmatic_source_directory,
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
    "archives", etc.), and a unique hash of the archives filter flags, return a the corresponding
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

    Currently, the only upgrade performed is renaming an archive or data check path that looks like:

      ~/.borgmatic/checks/1234567890/archives

    to:

      ~/.borgmatic/checks/1234567890/archives/all
    '''
    for check_type in ('archives', 'data'):
        new_path = make_check_time_path(config, borg_repository_id, check_type, 'all')
        old_path = os.path.dirname(new_path)
        temporary_path = f'{old_path}.temp'

        if not os.path.isfile(old_path) and not os.path.isfile(temporary_path):
            continue

        logger.debug(f'Upgrading archives check time from {old_path} to {new_path}')

        try:
            os.rename(old_path, temporary_path)
        except FileNotFoundError:
            pass

        os.mkdir(old_path)
        os.rename(temporary_path, new_path)


def run_check(
    config_filename,
    repository,
    config,
    hook_context,
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

    borgmatic.hooks.command.execute_hook(
        config.get('before_check'),
        config.get('umask'),
        config_filename,
        'pre-check',
        global_arguments.dry_run,
        **hook_context,
    )

    logger.info(f'{repository.get("label", repository["path"])}: Running consistency checks')
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
            write_check_time(
                make_check_time_path(config, repository_id, check, archives_check_id)
            )

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

    #if 'spot' in checks:
        # TODO:
        # count the number of files in source directories
        # in a loop until the sample percentage (of the total source files) is met:
            # pick a random file from source directories and calculate its sha256 sum
            # extract the file from the latest archive (to stdout) and calculate its sha256 sum
            # if the two checksums are equal, increment the matching files count
        # if the percentage of matching files (of the total source files) < tolerance percentage, error

    borgmatic.hooks.command.execute_hook(
        config.get('after_check'),
        config.get('umask'),
        config_filename,
        'post-check',
        global_arguments.dry_run,
        **hook_context,
    )
