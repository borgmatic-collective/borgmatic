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


logger = logging.getLogger(__name__)


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

    for check_config in config['checks']:
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
                    f"Skipping {check} check due to day of the week; check only runs on {'/'.join(day.title() for day in days)} (use --force to check anyway)",
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
                f'Skipping {check} check due to configured frequency; {remaining} until next check (use --force to check anyway)',
            )
            filtered_checks.remove(check)

    return tuple(filtered_checks)


def make_check_time_path(config, borg_repository_id, check_type, archives_check_id=None):
    '''
    Given a configuration dict, a Borg repository ID, the name of a check type ("repository",
    "archives", etc.), and a unique hash of the archives filter flags, return a path for recording
    that check's time (the time of that check last occurring).
    '''
    borgmatic_state_directory = borgmatic.config.paths.get_borgmatic_state_directory(config)

    if check_type in {'archives', 'data'}:
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
    pathlib.Path(path).touch(mode=0o600)


def read_check_time(path):
    '''
    Return the check time based on the modification time of the given path. Return None if the path
    doesn't exist.
    '''
    logger.debug(f'Reading check time from {path}')

    try:
        return datetime.datetime.fromtimestamp(os.stat(path).st_mtime)  # noqa: DTZ006
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
            ),
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
        borgmatic.config.paths.get_borgmatic_source_directory(config),
        'checks',
    )
    borgmatic_state_path = borgmatic.config.paths.get_borgmatic_state_directory(config)
    borgmatic_state_checks_path = os.path.join(borgmatic_state_path, 'checks')

    if os.path.exists(borgmatic_source_checks_path) and not os.path.exists(
        borgmatic_state_checks_path,
    ):
        logger.debug(
            f'Upgrading archives check times directory from {borgmatic_source_checks_path} to {borgmatic_state_checks_path}',
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

        with contextlib.suppress(FileNotFoundError):
            shutil.move(old_path, temporary_path)

        os.mkdir(old_path)
        shutil.move(temporary_path, new_path)
