import argparse
import datetime
import json
import logging
import os
import pathlib

from borgmatic.borg import environment, extract, feature, flags, rinfo, state
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

DEFAULT_CHECKS = (
    {'name': 'repository', 'frequency': '1 month'},
    {'name': 'archives', 'frequency': '1 month'},
)
DEFAULT_PREFIX = '{hostname}-'


logger = logging.getLogger(__name__)


def parse_checks(consistency_config, only_checks=None):
    '''
    Given a consistency config with a "checks" sequence of dicts and an optional list of override
    checks, return a tuple of named checks to run.

    For example, given a retention config of:

        {'checks': ({'name': 'repository'}, {'name': 'archives'})}

    This will be returned as:

        ('repository', 'archives')

    If no "checks" option is present in the config, return the DEFAULT_CHECKS. If a checks value
    has a name of "disabled", return an empty tuple, meaning that no checks should be run.
    '''
    checks = only_checks or tuple(
        check_config['name']
        for check_config in (consistency_config.get('checks', None) or DEFAULT_CHECKS)
    )
    checks = tuple(check.lower() for check in checks)
    if 'disabled' in checks:
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
    location_config, consistency_config, borg_repository_id, checks, force
):
    '''
    Given a location config, a consistency config with a "checks" sequence of dicts, a Borg
    repository ID, a sequence of checks, and whether to force checks to run, filter down those
    checks based on the configured "frequency" for each check as compared to its check time file.

    In other words, a check whose check time file's timestamp is too new (based on the configured
    frequency) will get cut from the returned sequence of checks. Example:

    consistency_config = {
        'checks': [
            {
                'name': 'archives',
                'frequency': '2 weeks',
            },
        ]
    }

    When this function is called with that consistency_config and "archives" in checks, "archives"
    will get filtered out of the returned result if its check time file is newer than 2 weeks old,
    indicating that it's not yet time to run that check again.

    Raise ValueError if a frequency cannot be parsed.
    '''
    filtered_checks = list(checks)

    if force:
        return tuple(filtered_checks)

    for check_config in consistency_config.get('checks', DEFAULT_CHECKS):
        check = check_config['name']
        if checks and check not in checks:
            continue

        frequency_delta = parse_frequency(check_config.get('frequency'))
        if not frequency_delta:
            continue

        check_time = read_check_time(
            make_check_time_path(location_config, borg_repository_id, check)
        )
        if not check_time:
            continue

        # If we've not yet reached the time when the frequency dictates we're ready for another
        # check, skip this check.
        if datetime.datetime.now() < check_time + frequency_delta:
            remaining = check_time + frequency_delta - datetime.datetime.now()
            logger.info(
                f"Skipping {check} check due to configured frequency; {remaining} until next check"
            )
            filtered_checks.remove(check)

    return tuple(filtered_checks)


def make_check_flags(local_borg_version, checks, check_last=None, prefix=None):
    '''
    Given the local Borg version and a parsed sequence of checks, transform the checks into tuple of
    command-line flags.

    For example, given parsed checks of:

        ('repository',)

    This will be returned as:

        ('--repository-only',)

    However, if both "repository" and "archives" are in checks, then omit them from the returned
    flags because Borg does both checks by default. If "data" is in checks, that implies "archives".

    Additionally, if a check_last value is given and "archives" is in checks, then include a
    "--last" flag. And if a prefix value is given and "archives" is in checks, then include a
    "--match-archives" flag.
    '''
    if 'archives' in checks:
        last_flags = ('--last', str(check_last)) if check_last else ()
        if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
            match_archives_flags = ('--match-archives', f'sh:{prefix}*') if prefix else ()
        else:
            match_archives_flags = ('--glob-archives', f'{prefix}*') if prefix else ()
    else:
        last_flags = ()
        match_archives_flags = ()
        if check_last:
            logger.info('Ignoring check_last option, as "archives" is not in consistency checks')
        if prefix:
            logger.info(
                'Ignoring consistency prefix option, as "archives" is not in consistency checks'
            )

    if 'data' in checks:
        data_flags = ('--verify-data',)
        checks += ('archives',)
    else:
        data_flags = ()

    common_flags = last_flags + match_archives_flags + data_flags

    if {'repository', 'archives'}.issubset(set(checks)):
        return common_flags

    return (
        tuple('--{}-only'.format(check) for check in checks if check in ('repository', 'archives'))
        + common_flags
    )


def make_check_time_path(location_config, borg_repository_id, check_type):
    '''
    Given a location configuration dict, a Borg repository ID, and the name of a check type
    ("repository", "archives", etc.), return a path for recording that check's time (the time of
    that check last occurring).
    '''
    return os.path.join(
        os.path.expanduser(
            location_config.get(
                'borgmatic_source_directory', state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY
            )
        ),
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


def check_archives(
    repository,
    location_config,
    storage_config,
    consistency_config,
    local_borg_version,
    local_path='borg',
    remote_path=None,
    progress=None,
    repair=None,
    only_checks=None,
    force=None,
):
    '''
    Given a local or remote repository path, a storage config dict, a consistency config dict,
    local/remote commands to run, whether to include progress information, whether to attempt a
    repair, and an optional list of checks to use instead of configured checks, check the contained
    Borg archives for consistency.

    If there are no consistency checks to run, skip running them.

    Raises ValueError if the Borg repository ID cannot be determined.
    '''
    try:
        borg_repository_id = json.loads(
            rinfo.display_repository_info(
                repository,
                storage_config,
                local_borg_version,
                argparse.Namespace(json=True),
                local_path,
                remote_path,
            )
        )['repository']['id']
    except (json.JSONDecodeError, KeyError):
        raise ValueError(f'Cannot determine Borg repository ID for {repository}')

    checks = filter_checks_on_frequency(
        location_config,
        consistency_config,
        borg_repository_id,
        parse_checks(consistency_config, only_checks),
        force,
    )
    check_last = consistency_config.get('check_last', None)
    lock_wait = None
    extra_borg_options = storage_config.get('extra_borg_options', {}).get('check', '')

    if set(checks).intersection({'repository', 'archives', 'data'}):
        lock_wait = storage_config.get('lock_wait', None)

        verbosity_flags = ()
        if logger.isEnabledFor(logging.INFO):
            verbosity_flags = ('--info',)
        if logger.isEnabledFor(logging.DEBUG):
            verbosity_flags = ('--debug', '--show-rc')

        prefix = consistency_config.get('prefix', DEFAULT_PREFIX)

        full_command = (
            (local_path, 'check')
            + (('--repair',) if repair else ())
            + make_check_flags(local_borg_version, checks, check_last, prefix)
            + (('--remote-path', remote_path) if remote_path else ())
            + (('--lock-wait', str(lock_wait)) if lock_wait else ())
            + verbosity_flags
            + (('--progress',) if progress else ())
            + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
            + flags.make_repository_flags(repository, local_borg_version)
        )

        borg_environment = environment.make_environment(storage_config)

        # The Borg repair option triggers an interactive prompt, which won't work when output is
        # captured. And progress messes with the terminal directly.
        if repair or progress:
            execute_command(
                full_command, output_file=DO_NOT_CAPTURE, extra_environment=borg_environment
            )
        else:
            execute_command(full_command, extra_environment=borg_environment)

        for check in checks:
            write_check_time(make_check_time_path(location_config, borg_repository_id, check))

    if 'extract' in checks:
        extract.extract_last_archive_dry_run(
            storage_config, local_borg_version, repository, lock_wait, local_path, remote_path
        )
        write_check_time(make_check_time_path(location_config, borg_repository_id, 'extract'))
