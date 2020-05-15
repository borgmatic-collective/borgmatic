import logging

from borgmatic.borg import extract
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

DEFAULT_CHECKS = ('repository', 'archives')
DEFAULT_PREFIX = '{hostname}-'


logger = logging.getLogger(__name__)


def _parse_checks(consistency_config, only_checks=None):
    '''
    Given a consistency config with a "checks" list, and an optional list of override checks,
    transform them a tuple of named checks to run.

    For example, given a retention config of:

        {'checks': ['repository', 'archives']}

    This will be returned as:

        ('repository', 'archives')

    If no "checks" option is present in the config, return the DEFAULT_CHECKS. If the checks value
    is the string "disabled", return an empty tuple, meaning that no checks should be run.

    If the "data" option is present, then make sure the "archives" option is included as well.
    '''
    checks = [
        check.lower() for check in (only_checks or consistency_config.get('checks', []) or [])
    ]
    if checks == ['disabled']:
        return ()

    if 'data' in checks and 'archives' not in checks:
        checks.append('archives')

    return tuple(check for check in checks if check not in ('disabled', '')) or DEFAULT_CHECKS


def _make_check_flags(checks, check_last=None, prefix=None):
    '''
    Given a parsed sequence of checks, transform it into tuple of command-line flags.

    For example, given parsed checks of:

        ('repository',)

    This will be returned as:

        ('--repository-only',)

    However, if both "repository" and "archives" are in checks, then omit them from the returned
    flags because Borg does both checks by default.

    Additionally, if a check_last value is given and "archives" is in checks, then include a
    "--last" flag. And if a prefix value is given and "archives" is in checks, then include a
    "--prefix" flag.
    '''
    if 'archives' in checks:
        last_flags = ('--last', str(check_last)) if check_last else ()
        prefix_flags = ('--prefix', prefix) if prefix else ()
    else:
        last_flags = ()
        prefix_flags = ()
        if check_last:
            logger.warning(
                'Ignoring check_last option, as "archives" is not in consistency checks.'
            )
        if prefix:
            logger.warning(
                'Ignoring consistency prefix option, as "archives" is not in consistency checks.'
            )

    common_flags = last_flags + prefix_flags + (('--verify-data',) if 'data' in checks else ())

    if set(DEFAULT_CHECKS).issubset(set(checks)):
        return common_flags

    return (
        tuple('--{}-only'.format(check) for check in checks if check in DEFAULT_CHECKS)
        + common_flags
    )


def check_archives(
    repository,
    storage_config,
    consistency_config,
    local_path='borg',
    remote_path=None,
    progress=None,
    repair=None,
    only_checks=None,
):
    '''
    Given a local or remote repository path, a storage config dict, a consistency config dict,
    local/remote commands to run, whether to include progress information, whether to attempt a
    repair, and an optional list of checks to use instead of configured checks, check the contained
    Borg archives for consistency.

    If there are no consistency checks to run, skip running them.
    '''
    checks = _parse_checks(consistency_config, only_checks)
    check_last = consistency_config.get('check_last', None)
    lock_wait = None
    extra_borg_options = storage_config.get('extra_borg_options', {}).get('check', '')

    if set(checks).intersection(set(DEFAULT_CHECKS + ('data',))):
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
            + _make_check_flags(checks, check_last, prefix)
            + (('--remote-path', remote_path) if remote_path else ())
            + (('--lock-wait', str(lock_wait)) if lock_wait else ())
            + verbosity_flags
            + (('--progress',) if progress else ())
            + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
            + (repository,)
        )

        # The Borg repair option trigger an interactive prompt, which won't work when output is
        # captured. And progress messes with the terminal directly.
        if repair or progress:
            execute_command(full_command, output_file=DO_NOT_CAPTURE)
        else:
            execute_command(full_command)

    if 'extract' in checks:
        extract.extract_last_archive_dry_run(repository, lock_wait, local_path, remote_path)
