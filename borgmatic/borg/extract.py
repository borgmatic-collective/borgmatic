import logging
import subprocess
import sys

from borgmatic.logger import get_logger

logger = get_logger(__name__)


def extract_last_archive_dry_run(repository, lock_wait=None, local_path='borg', remote_path=None):
    '''
    Perform an extraction dry-run of the most recent archive. If there are no archives, skip the
    dry-run.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    lock_wait_flags = ('--lock-wait', str(lock_wait)) if lock_wait else ()
    verbosity_flags = ()
    if logger.isEnabledFor(logging.DEBUG):
        verbosity_flags = ('--debug', '--show-rc')
    elif logger.isEnabledFor(logging.INFO):
        verbosity_flags = ('--info',)

    full_list_command = (
        (local_path, 'list', '--short', repository)
        + remote_path_flags
        + lock_wait_flags
        + verbosity_flags
    )

    list_output = subprocess.check_output(full_list_command).decode(sys.stdout.encoding)

    last_archive_name = list_output.strip().split('\n')[-1]
    if not last_archive_name:
        return

    list_flag = ('--list',) if logger.isEnabledFor(logging.DEBUG) else ()
    full_extract_command = (
        (
            local_path,
            'extract',
            '--dry-run',
            '{repository}::{last_archive_name}'.format(
                repository=repository, last_archive_name=last_archive_name
            ),
        )
        + remote_path_flags
        + lock_wait_flags
        + verbosity_flags
        + list_flag
    )

    logger.debug(' '.join(full_extract_command))
    subprocess.check_call(full_extract_command)


def extract_archive(
    dry_run,
    repository,
    archive,
    restore_paths,
    location_config,
    storage_config,
    local_path='borg',
    remote_path=None,
    progress=False,
):
    '''
    Given a dry-run flag, a local or remote repository path, an archive name, zero or more paths to
    restore from the archive, and location/storage configuration dicts, extract the archive into the
    current directory.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'extract', '::'.join((repository, archive)))
        + (tuple(restore_paths) if restore_paths else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--numeric-owner',) if location_config.get('numeric_owner') else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--list', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (('--progress',) if progress else ())
    )

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
