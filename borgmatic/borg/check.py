import logging
import os
import subprocess

from borgmatic.borg import extract


DEFAULT_CHECKS = ('repository', 'archives')
DEFAULT_PREFIX = '{hostname}-'


logger = logging.getLogger(__name__)


def _parse_checks(consistency_config):
    '''
    Given a consistency config with a "checks" list, transform it to a tuple of named checks to run.

    For example, given a retention config of:

        {'checks': ['repository', 'archives']}

    This will be returned as:

        ('repository', 'archives')

    If no "checks" option is present, return the DEFAULT_CHECKS. If the checks value is the string
    "disabled", return an empty tuple, meaning that no checks should be run.
    '''
    checks = consistency_config.get('checks', [])
    if checks == ['disabled']:
        return ()

    return (
        tuple(check for check in checks if check.lower() not in ('disabled', '')) or DEFAULT_CHECKS
    )


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
        prefix_flags = ('--prefix', prefix) if prefix else ('--prefix', DEFAULT_PREFIX)
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

    if set(DEFAULT_CHECKS).issubset(set(checks)):
        return last_flags + prefix_flags

    return (
        tuple('--{}-only'.format(check) for check in checks if check in DEFAULT_CHECKS)
        + last_flags
        + prefix_flags
    )


def check_archives(
    repository, storage_config, consistency_config, local_path='borg', remote_path=None
):
    '''
    Given a local or remote repository path, a storage config dict, a consistency config dict,
    and a local/remote commands to run, check the contained Borg archives for consistency.

    If there are no consistency checks to run, skip running them.
    '''
    checks = _parse_checks(consistency_config)
    check_last = consistency_config.get('check_last', None)
    lock_wait = None

    if set(checks).intersection(set(DEFAULT_CHECKS)):
        remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
        lock_wait = storage_config.get('lock_wait', None)
        lock_wait_flags = ('--lock-wait', str(lock_wait)) if lock_wait else ()

        verbosity_flags = ()
        if logger.isEnabledFor(logging.INFO):
            verbosity_flags = ('--info',)
        if logger.isEnabledFor(logging.DEBUG):
            verbosity_flags = ('--debug', '--show-rc')

        prefix = consistency_config.get('prefix')

        full_command = (
            (local_path, 'check', repository)
            + _make_check_flags(checks, check_last, prefix)
            + remote_path_flags
            + lock_wait_flags
            + verbosity_flags
        )

        # The check command spews to stdout/stderr even without the verbose flag. Suppress it.
        stdout = None if verbosity_flags else open(os.devnull, 'w')

        logger.debug(' '.join(full_command))
        subprocess.check_call(full_command, stdout=stdout, stderr=subprocess.STDOUT)

    if 'extract' in checks:
        extract.extract_last_archive_dry_run(repository, lock_wait, local_path, remote_path)
