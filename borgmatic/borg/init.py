import logging
import subprocess


logger = logging.getLogger(__name__)


def initialize_repository(
    repository,
    encryption_mode,
    append_only=None,
    storage_quota=None,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a Borg encryption mode, whether the repository should
    be append-only, and the storage quota to use, initialize the repository.
    '''
    full_command = (
        (local_path, 'init', repository)
        + (('--encryption', encryption_mode) if encryption_mode else ())
        + (('--append-only',) if append_only else ())
        + (('--storage-quota', storage_quota) if storage_quota else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug',) if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--remote-path', remote_path) if remote_path else ())
    )

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
