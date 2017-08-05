from datetime import datetime
import glob
import itertools
import os
import platform
import subprocess
import tempfile

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


def initialize(storage_config):
    passphrase = storage_config.get('encryption_passphrase')

    if passphrase:
        os.environ['BORG_PASSPHRASE'] = passphrase


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
    verbosity, repository, location_config, storage_config,
):
    '''
    Given a vebosity flag, a storage config dict, a list of source directories, a local or remote
    repository path, a list of exclude patterns, create a Borg archive.
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
        'borg', 'create',
        '{repository}::{hostname}-{timestamp}'.format(
            repository=repository,
            hostname=platform.node(),
            timestamp=datetime.now().isoformat(),
        ),
    ) + sources + exclude_flags + compression_flags + one_file_system_flags + \
        remote_path_flags + umask_flags + verbosity_flags

    subprocess.check_call(full_command)
