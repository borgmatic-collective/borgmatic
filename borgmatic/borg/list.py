import logging
import subprocess


logger = logging.getLogger(__name__)


def list_archives(repository, storage_config, local_path='borg', remote_path=None, json=False):
    '''
    Given a local or remote repository path, and a storage config dict,
    list Borg archives in the repository.
    '''
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'list', repository)
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--json',) if json else ())
    )
    logger.debug(' '.join(full_command))

    output = subprocess.check_output(full_command)
    return output.decode() if output is not None else None
