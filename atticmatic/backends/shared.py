from datetime import datetime
import os
import platform
import subprocess

from atticmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


# Common backend functionality shared by Attic and Borg. As the two backup
# commands diverge, these shared functions will likely need to be replaced
# with non-shared functions within atticmatic.backends.attic and
# atticmatic.backends.borg.


def create_archive(excludes_filename, verbosity, source_directories, repository, command):
    '''
    Given an excludes filename, a vebosity flag, a space-separated list of source directories, a
    local or remote repository path, and a command to run, create an attic archive.
    '''
    sources = tuple(source_directories.split(' '))
    verbosity_flags = {
        VERBOSITY_SOME: ('--stats',),
        VERBOSITY_LOTS: ('--verbose', '--stats'),
    }.get(verbosity, ())

    full_command = (
        command, 'create',
        '--exclude-from', excludes_filename,
        '{repo}::{hostname}-{timestamp}'.format(
            repo=repository,
            hostname=platform.node(),
            timestamp=datetime.now().isoformat(),
        ),
    ) + sources + verbosity_flags

    subprocess.check_call(full_command)


def _make_prune_flags(retention_config):
    '''
    Given a retention config dict mapping from option name to value, tranform it into an iterable of
    command-line name-value flag pairs.

    For example, given a retention config of:

        {'keep_weekly': 4, 'keep_monthly': 6}

    This will be returned as an iterable of:

        (
            ('--keep-weekly', '4'),
            ('--keep-monthly', '6'),
        )
    '''
    return (
        ('--' + option_name.replace('_', '-'), str(retention_config[option_name]))
        for option_name, value in retention_config.items()
    )


def prune_archives(verbosity, repository, retention_config, command):
    '''
    Given a verbosity flag, a local or remote repository path, a retention config dict, and a
    command to run, prune attic archives according the the retention policy specified in that
    configuration.
    '''
    verbosity_flags = {
        VERBOSITY_SOME: ('--stats',),
        VERBOSITY_LOTS: ('--verbose', '--stats'),
    }.get(verbosity, ())

    full_command = (
        command, 'prune',
        repository,
    ) + tuple(
        element
        for pair in _make_prune_flags(retention_config)
        for element in pair
    ) + verbosity_flags

    subprocess.check_call(full_command)


DEFAULT_CHECKS = ('repository', 'archives')


def _parse_checks(consistency_config):
    '''
    Given a consistency config with a space-separated "checks" option, transform it to a tuple of
    named checks to run.

    For example, given a retention config of:

        {'checks': 'repository archives'}

    This will be returned as:

        ('repository', 'archives')

    If no "checks" option is present, return the DEFAULT_CHECKS. If the checks value is the string
    "disabled", return an empty tuple, meaning that no checks should be run.
    '''
    checks = consistency_config.get('checks', '').strip()
    if not checks:
        return DEFAULT_CHECKS

    return tuple(
        check for check in consistency_config['checks'].split(' ')
        if check.lower() not in ('disabled', '')
    )


def _make_check_flags(checks):
    '''
    Given a parsed sequence of checks, transform it into tuple of command-line flags.

    For example, given parsed checks of:

        ('repository',)

    This will be returned as:
    
        ('--repository-only',)
    '''
    if checks == DEFAULT_CHECKS:
        return ()

    return tuple(
        '--{}-only'.format(check) for check in checks
    )


def check_archives(verbosity, repository, consistency_config, command):
    '''
    Given a verbosity flag, a local or remote repository path, a consistency config dict, and a
    command to run, check the contained attic archives for consistency.

    If there are no consistency checks to run, skip running them.
    '''
    checks = _parse_checks(consistency_config)
    if not checks:
        return

    verbosity_flags = {
        VERBOSITY_SOME: ('--verbose',),
        VERBOSITY_LOTS: ('--verbose',),
    }.get(verbosity, ())

    full_command = (
        command, 'check',
        repository,
    ) + _make_check_flags(checks) + verbosity_flags

    # The check command spews to stdout even without the verbose flag. Suppress it.
    stdout = None if verbosity_flags else open(os.devnull, 'w')

    subprocess.check_call(full_command, stdout=stdout)
