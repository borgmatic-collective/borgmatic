from datetime import datetime
import os
import platform
import subprocess


def create_archive(excludes_filename, verbose, source_directories, repository):
    '''
    Given an excludes filename, a vebosity flag, a space-separated list of source directories, and
    a local or remote repository path, create an attic archive.
    '''
    sources = tuple(source_directories.split(' '))

    command = (
        'attic', 'create',
        '--exclude-from', excludes_filename,
        '{repo}::{hostname}-{timestamp}'.format(
            repo=repository,
            hostname=platform.node(),
            timestamp=datetime.now().isoformat(),
        ),
    ) + sources + (
        ('--verbose', '--stats') if verbose else ()
    )

    subprocess.check_call(command)


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


def prune_archives(verbose, repository, retention_config):
    '''
    Given a verbosity flag, a local or remote repository path, and a retention config dict, prune
    attic archives according the the retention policy specified in that configuration.
    '''
    command = (
        'attic', 'prune',
        repository,
    ) + tuple(
        element
        for pair in _make_prune_flags(retention_config)
        for element in pair
    ) + (('--verbose',) if verbose else ())

    subprocess.check_call(command)


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


def check_archives(verbose, repository, consistency_config):
    '''
    Given a verbosity flag, a local or remote repository path, and a consistency config dict, check
    the contained attic archives for consistency.

    If there are no consistency checks to run, skip running them.
    '''
    checks = _parse_checks(consistency_config)
    if not checks:
        return

    command = (
        'attic', 'check',
        repository,
    ) + _make_check_flags(checks) + (('--verbose',) if verbose else ())

    # Attic's check command spews to stdout even without the verbose flag. Suppress it.
    stdout = None if verbose else open(os.devnull, 'w')

    subprocess.check_call(command, stdout=stdout)
