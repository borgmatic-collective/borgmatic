from datetime import datetime
import glob
import itertools
import os
import platform
import sys
import re
import subprocess
import tempfile

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


# Integration with Borg for actually handling backups.


COMMAND = 'borg'


def initialize(storage_config, command=COMMAND):
    passphrase = storage_config.get('encryption_passphrase')

    if passphrase:
        os.environ['{}_PASSPHRASE'.format(command.upper())] = passphrase


def _write_exclude_file(exclude_patterns=None):
    '''
    Given a sequence of exclude patterns, write them to a named temporary file and return it. Return
    None if no patterns are provided.
    '''
    if not exclude_patterns:
        return None

    exclude_file = tempfile.NamedTemporaryFile('w')
    exclude_file.write('\n'.join(exclude_patterns))
    exclude_file.flush()

    return exclude_file


def create_archive(
    verbosity, repository, location_config, storage_config, command=COMMAND,
):
    '''
    Given a vebosity flag, a storage config dict, a list of source directories, a local or remote
    repository path, a list of exclude patterns, and a command to run, create a Borg archive.
    '''
    sources = tuple(
        itertools.chain.from_iterable(
            glob.glob(directory) or [directory]
            for directory in location_config['source_directories']
        )
    )

    exclude_file = _write_exclude_file(location_config.get('exclude_patterns'))
    exclude_flags = ('--exclude-from', exclude_file.name) if exclude_file else ()
    compression = storage_config.get('compression', None)
    compression_flags = ('--compression', compression) if compression else ()
    umask = storage_config.get('umask', None)
    umask_flags = ('--umask', str(umask)) if umask else ()
    one_file_system_flags = ('--one-file-system',) if location_config.get('one_file_system') else ()
    remote_path = location_config.get('remote_path')
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--list', '--stats'),
    }.get(verbosity, ())

    full_command = (
        command, 'create',
        '{repository}::{hostname}-{timestamp}'.format(
            repository=repository,
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
    command to run, prune Borg archives according the the retention policy specified in that
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


def check_archives(verbosity, repository, consistency_config, command=COMMAND, remote_path=None):
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
            command, 'check',
            repository,
        ) + _make_check_flags(checks, check_last) + remote_path_flags + verbosity_flags

        # The check command spews to stdout/stderr even without the verbose flag. Suppress it.
        stdout = None if verbosity_flags else open(os.devnull, 'w')

        subprocess.check_call(full_command, stdout=stdout, stderr=subprocess.STDOUT)

    if 'extract' in checks:
        extract_last_archive_dry_run(verbosity, repository, command, remote_path)


def extract_last_archive_dry_run(verbosity, repository, command=COMMAND, remote_path=None):
    '''
    Perform an extraction dry-run of just the most recent archive. If there are no archives, skip
    the dry-run.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info',),
        VERBOSITY_LOTS: ('--debug',),
    }.get(verbosity, ())

    full_list_command = (
        command, 'list',
        '--short',
        repository,
    ) + remote_path_flags + verbosity_flags

    list_output = subprocess.check_output(full_list_command).decode(sys.stdout.encoding)

    last_archive_name = list_output.strip().split('\n')[-1]
    if not last_archive_name:
        return

    list_flag = ('--list',) if verbosity == VERBOSITY_LOTS else ()
    full_extract_command = (
        command, 'extract',
        '--dry-run',
        '{repository}::{last_archive_name}'.format(
            repository=repository,
            last_archive_name=last_archive_name,
        ),
    ) + remote_path_flags + verbosity_flags + list_flag

    subprocess.check_call(full_extract_command)
