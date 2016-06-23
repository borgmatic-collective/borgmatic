from datetime import datetime
import os
import re
import platform
import subprocess
from glob import glob
from itertools import chain

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


# Integration with Borg for actually handling backups.


COMMAND = 'borg'


def initialize(storage_config, command=COMMAND):
    passphrase = storage_config.get('encryption_passphrase')

    if passphrase:
        os.environ['{}_PASSPHRASE'.format(command.upper())] = passphrase


def create_archive(
    excludes_filename, verbosity, storage_config, source_directories, repository, command=COMMAND,
    one_file_system=None, remote_path=None,
):
    '''
    Given an excludes filename (or None), a vebosity flag, a storage config dict, a space-separated
    list of source directories, a local or remote repository path, and a command to run, create an
    attic archive.
    '''
    sources = re.split('\s+', source_directories)
    sources = tuple(chain.from_iterable(glob(x) or [x] for x in sources))
    exclude_flags = ('--exclude-from', excludes_filename) if excludes_filename else ()
    compression = storage_config.get('compression', None)
    compression_flags = ('--compression', compression) if compression else ()
    umask = storage_config.get('umask', None)
    umask_flags = ('--umask', str(umask)) if umask else ()
    one_file_system_flags = ('--one-file-system',) if one_file_system else ()
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--list', '--stats'),
    }.get(verbosity, ())

    full_command = (
        command, 'create',
        '{repo}::{hostname}-{timestamp}'.format(
            repo=repository,
            hostname=platform.node(),
            timestamp=datetime.now().isoformat(),
        ),
    ) + sources + exclude_flags + compression_flags + one_file_system_flags + \
        remote_path_flags + umask_flags + verbosity_flags

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


def prune_archives(verbosity, repository, retention_config, command=COMMAND, remote_path=None):
    '''
    Given a verbosity flag, a local or remote repository path, a retention config dict, and a
    command to run, prune attic archives according the the retention policy specified in that
    configuration.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--stats'),
    }.get(verbosity, ())

    full_command = (
        command, 'prune',
        repository,
    ) + tuple(
        element
        for pair in _make_prune_flags(retention_config)
        for element in pair
    ) + remote_path_flags + verbosity_flags

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


def _make_check_flags(checks, check_last=None):
    '''
    Given a parsed sequence of checks, transform it into tuple of command-line flags.

    For example, given parsed checks of:

        ('repository',)

    This will be returned as:

        ('--repository-only',)

    Additionally, if a check_last value is given, a "--last" flag will be added. Note that only
    Borg supports this flag.
    '''
    last_flag = ('--last', check_last) if check_last else ()
    if checks == DEFAULT_CHECKS:
        return last_flag

    return tuple(
        '--{}-only'.format(check) for check in checks
    ) + last_flag


def check_archives(verbosity, repository, consistency_config, command=COMMAND, remote_path=None):
    '''
    Given a verbosity flag, a local or remote repository path, a consistency config dict, and a
    command to run, check the contained attic archives for consistency.

    If there are no consistency checks to run, skip running them.
    '''
    checks = _parse_checks(consistency_config)
    check_last = consistency_config.get('check_last', None)
    if not checks:
        return

    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info',),
        VERBOSITY_LOTS: ('--debug',),
    }.get(verbosity, ())

    full_command = (
        command, 'check',
        repository,
    ) + _make_check_flags(checks, check_last) + remote_path_flags + verbosity_flags

    # The check command spews to stdout/stderr even without the verbose flag. Suppress it.
    stdout = None if verbosity_flags else open(os.devnull, 'w')

    subprocess.check_call(full_command, stdout=stdout, stderr=subprocess.STDOUT)
