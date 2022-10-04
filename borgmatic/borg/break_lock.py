import logging

from borgmatic.borg import environment, flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def break_lock(
    repository, storage_config, local_borg_version, local_path='borg', remote_path=None,
):
    '''
    Given a local or remote repository path, a storage configuration dict, the local Borg version,
    and optional local and remote Borg paths, break any repository and cache locks leftover from Borg
    aborting.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'break-lock')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_repository_flags(repository, local_borg_version)
    )

    borg_environment = environment.make_environment(storage_config)
    execute_command(full_command, borg_local_path=local_path, extra_environment=borg_environment)
