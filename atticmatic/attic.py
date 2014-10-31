from datetime import datetime

import platform
import subprocess


def create_archive(excludes_filename, verbose, source_directories, repository):
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


def prune_archives(repository, verbose, keep_daily, keep_weekly, keep_monthly):
    command = (
        'attic', 'prune',
        repository,
        '--keep-daily', str(keep_daily),
        '--keep-weekly', str(keep_weekly),
        '--keep-monthly', str(keep_monthly),
    ) + (('--verbose',) if verbose else ())

    subprocess.check_call(command)
