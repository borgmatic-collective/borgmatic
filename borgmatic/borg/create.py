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
    sources = tuple(
        itertools.chain.from_iterable(
            _expand_directory(directory)
            for directory in location_config['source_directories']
        )
    )

    pattern_file = _write_pattern_file(location_config.get('patterns'))
    pattern_flags = _make_pattern_flags(
        location_config,
        pattern_file.name if pattern_file else None,
    )
    exclude_file = _write_pattern_file(location_config.get('exclude_patterns'))
    exclude_flags = _make_exclude_flags(
        location_config,
        exclude_file.name if exclude_file else None,
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
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--list', '--stats'),
    }.get(verbosity, ())
    dry_run_flags = ('--dry-run',) if dry_run else ()
    default_archive_name_format = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'
    archive_name_format = storage_config.get('archive_name_format', default_archive_name_format)

    full_command = (
        local_path, 'create',
        '{repository}::{archive_name_format}'.format(
            repository=repository,
            archive_name_format=archive_name_format,
        ),
    ) + sources + pattern_flags + exclude_flags + compression_flags + remote_rate_limit_flags + \
        one_file_system_flags + files_cache_flags + remote_path_flags + umask_flags + \
        verbosity_flags + dry_run_flags

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
