import glob
import itertools
import logging
import os
import subprocess
import tempfile

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


logger = logging.getLogger(__name__)


def initialize_environment(storage_config):
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


def _make_exclude_flags(location_config, exclude_patterns_filename=None):
    '''
    Given a location config dict with various exclude options, and a filename containing any exclude
    patterns, return the corresponding Borg flags as a tuple.
    '''
    exclude_filenames = tuple(location_config.get('exclude_from') or ()) + (
        (exclude_patterns_filename,) if exclude_patterns_filename else ()
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
    verbosity, repository, location_config, storage_config,
):
    '''
    Given a vebosity flag, a local or remote repository path, a location config dict, and a storage
    config dict, create a Borg archive.
    '''
    sources = tuple(
        itertools.chain.from_iterable(
            _expand_directory(directory)
            for directory in location_config['source_directories']
        )
    )

    exclude_patterns_file = _write_exclude_file(location_config.get('exclude_patterns'))
    exclude_flags = _make_exclude_flags(
        location_config,
        exclude_patterns_file.name if exclude_patterns_file else None,
    )
    compression = storage_config.get('compression', None)
    compression_flags = ('--compression', compression) if compression else ()
    remote_rate_limit = storage_config.get('remote_rate_limit', None)
    remote_rate_limit_flags = ('--remote-ratelimit', str(remote_rate_limit)) if remote_rate_limit else ()
    umask = storage_config.get('umask', None)
    umask_flags = ('--umask', str(umask)) if umask else ()
    one_file_system_flags = ('--one-file-system',) if location_config.get('one_file_system') else ()
    files_cache = location_config.get('files_cache')
    files_cache_flags = ('--files-cache', files_cache) if files_cache else ()
    remote_path = location_config.get('remote_path')
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--list', '--stats'),
    }.get(verbosity, ())
    default_archive_name_format = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'
    archive_name_format = storage_config.get('archive_name_format', default_archive_name_format)

    full_command = (
        'borg', 'create',
        '{repository}::{archive_name_format}'.format(
            repository=repository,
            archive_name_format=archive_name_format,
        ),
    ) + sources + exclude_flags + compression_flags + remote_rate_limit_flags + \
        one_file_system_flags + files_cache_flags + remote_path_flags + umask_flags + \
        verbosity_flags

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
