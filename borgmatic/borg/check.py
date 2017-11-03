import logging
import os
import subprocess

from borgmatic.borg import extract
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


DEFAULT_CHECKS = ('repository', 'archives')


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

    return tuple(check for check in checks if check.lower() not in ('disabled', '')) or DEFAULT_CHECKS


def _make_check_flags(checks, check_last=None):
    '''
    Given a parsed sequence of checks, transform it into tuple of command-line flags.

    For example, given parsed checks of:

        ('repository',)

    This will be returned as:

        ('--repository-only',)

    Additionally, if a check_last value is given, a "--last" flag will be added.
    '''
    last_flag = ('--last', str(check_last)) if check_last else ()
    if checks == DEFAULT_CHECKS:
        return last_flag

    return tuple(
        '--{}-only'.format(check) for check in checks
        if check in DEFAULT_CHECKS
    ) + last_flag


def check_archives(verbosity, repository, consistency_config, remote_path=None):
    '''
    Given a verbosity flag, a local or remote repository path, a consistency config dict, and a
    command to run, check the contained Borg archives for consistency.

    If there are no consistency checks to run, skip running them.
    '''
    checks = _parse_checks(consistency_config)
    check_last = consistency_config.get('check_last', None)

    if set(checks).intersection(set(DEFAULT_CHECKS)):
        remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
        verbosity_flags = {
            VERBOSITY_SOME: ('--info',),
            VERBOSITY_LOTS: ('--debug',),
        }.get(verbosity, ())

        full_command = (
            'borg', 'check',
            repository,
        ) + _make_check_flags(checks, check_last) + remote_path_flags + verbosity_flags

        # The check command spews to stdout/stderr even without the verbose flag. Suppress it.
        stdout = None if verbosity_flags else open(os.devnull, 'w')

        logger.debug(' '.join(full_command))
        subprocess.check_call(full_command, stdout=stdout, stderr=subprocess.STDOUT)

    if 'extract' in checks:
        extract.extract_last_archive_dry_run(verbosity, repository, remote_path)
