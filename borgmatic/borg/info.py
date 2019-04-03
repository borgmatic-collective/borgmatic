import logging

from borgmatic.borg.execute import execute_command


logger = logging.getLogger(__name__)


def display_archives_info(
    repository, storage_config, local_path='borg', remote_path=None, json=False
):
    '''
    Given a local or remote repository path, and a storage config dict, display summary information
    for Borg archives in the repository or return JSON summary information.
    '''
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'info', repository)
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--json',) if json else ())
    )

    return execute_command(full_command, capture_output=json)
