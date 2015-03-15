from __future__ import print_function
from datetime import datetime
import os
import platform
import re
import subprocess
import sys


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

    try:
        subprocess.check_output(command, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, error:
        print(error.output.strip(), file=sys.stderr)

        if re.search('Error: Repository .* does not exist', error.output):
            raise RuntimeError('To create a repository, run: attic init --encryption=keyfile {}'.format(repository))
        raise error


def make_prune_flags(retention_config):
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
        for pair in make_prune_flags(retention_config)
        for element in pair
    ) + (('--verbose',) if verbose else ())

    subprocess.check_call(command)


def check_archives(verbose, repository):
    '''
    Given a verbosity flag and a local or remote repository path, check the contained attic archives
    for consistency.
    '''
    command = (
        'attic', 'check',
        repository,
    ) + (('--verbose',) if verbose else ())

    # Attic's check command spews to stdout even without the verbose flag. Suppress it.
    stdout = None if verbose else open(os.devnull, 'w')

    subprocess.check_call(command, stdout=stdout)
