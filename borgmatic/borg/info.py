import logging

from borgmatic.execute import execute_command
from borgmatic.logger import get_logger

logger = get_logger(__name__)


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
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO and not json else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) and not json else ())
        + (('--json',) if json else ())
    )

    return execute_command(full_command, output_log_level=None if json else logging.WARNING)
