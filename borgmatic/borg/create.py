import glob
import itertools
import logging
import os
import subprocess
import tempfile

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


logger = logging.getLogger(__name__)


def initialize_environment(storage_config):
    passcommand = storage_config.get('encryption_passcommand')
    if passcommand:
        os.environ['BORG_PASSCOMMAND'] = passcommand

    passphrase = storage_config.get('encryption_passphrase')
    if passphrase:
        os.environ['BORG_PASSPHRASE'] = passphrase

    ssh_command = storage_config.get('ssh_command')
    if ssh_command:
        os.environ['BORG_RSH'] = ssh_command


def _expand_directory(directory):
    '''
    Given a directory path, expand any tilde (representing a user's home directory) and any globs
    therein. Return a list of one or more resulting paths.
    '''
    expanded_directory = os.path.expanduser(directory)

    return glob.glob(expanded_directory) or [expanded_directory]


def _expand_directories(directories):
    '''
    Given a sequence of directory paths, expand tildes and globs in each one. Return all the
    resulting directories as a single flattened tuple.
    '''
    if directories is None:
        return ()

    return tuple(
        itertools.chain.from_iterable(
            _expand_directory(directory)
            for directory in directories
        )
    )


def _write_pattern_file(patterns=None):
    '''
    Given a sequence of patterns, write them to a named temporary file and return it. Return None
    if no patterns are provided.
    '''
    if not patterns:
        return None

    pattern_file = tempfile.NamedTemporaryFile('w')
    pattern_file.write('\n'.join(patterns))
    pattern_file.flush()

    return pattern_file


def _make_pattern_flags(location_config, pattern_filename=None):
    '''
    Given a location config dict with a potential pattern_from option, and a filename containing any
    additional patterns, return the corresponding Borg flags for those files as a tuple.
    '''
    pattern_filenames = tuple(location_config.get('patterns_from') or ()) + (
        (pattern_filename,) if pattern_filename else ()
    )

    return tuple(
        itertools.chain.from_iterable(
            ('--patterns-from', pattern_filename)
            for pattern_filename in pattern_filenames
        )
    )


def _make_exclude_flags(location_config, exclude_filename=None):
    '''
    Given a location config dict with various exclude options, and a filename containing any exclude
    patterns, return the corresponding Borg flags as a tuple.
    '''
    exclude_filenames = tuple(location_config.get('exclude_from') or ()) + (
        (exclude_filename,) if exclude_filename else ()
    )
    exclude_from_flags = tuple(
        itertools.chain.from_iterable(
            ('--exclude-from', exclude_filename)
            for exclude_filename in exclude_filenames
        )
    )
    caches_flag = ('--exclude-caches',) if location_config.get('exclude_caches') else ()
    if_present = location_config.get('exclude_if_present')
    if_present_flags = ('--exclude-if-present', if_present) if if_present else ()

    return exclude_from_flags + caches_flag + if_present_flags


def create_archive(
    verbosity, dry_run, repository, location_config, storage_config, local_path='borg', remote_path=None,
):
    '''
    Given vebosity/dry-run flags, a local or remote repository path, a location config dict, and a
    storage config dict, create a Borg archive.
    '''
    sources = _expand_directories(location_config['source_directories'])

    pattern_file = _write_pattern_file(location_config.get('patterns'))
    exclude_file = _write_pattern_file(_expand_directories(location_config.get('exclude_patterns')))
    compression = storage_config.get('compression', None)
    remote_rate_limit = storage_config.get('remote_rate_limit', None)
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)
    files_cache = location_config.get('files_cache')
    default_archive_name_format = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'
    archive_name_format = storage_config.get('archive_name_format', default_archive_name_format)

    full_command = (
        (
            local_path, 'create',
            '{repository}::{archive_name_format}'.format(
                repository=repository,
                archive_name_format=archive_name_format,
            ),
        )
        + sources
        + _make_pattern_flags(
            location_config,
            pattern_file.name if pattern_file else None,
        )
        + _make_exclude_flags(
            location_config,
            exclude_file.name if exclude_file else None,
        )
        + (('--compression', compression) if compression else ())
        + (('--remote-ratelimit', str(remote_rate_limit)) if remote_rate_limit else ())
        + (('--one-file-system',) if location_config.get('one_file_system') else ())
        + (('--nobsdflags',) if location_config.get('bsd_flags') is False else ())
        + (('--files-cache', files_cache) if files_cache else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + {
            VERBOSITY_SOME: ('--info',) if dry_run else ('--info', '--stats',),
            VERBOSITY_LOTS: ('--debug', '--list',) if dry_run else ('--debug', '--list', '--stats',),
        }.get(verbosity, ())
        + (('--dry-run',) if dry_run else ())
    )

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
