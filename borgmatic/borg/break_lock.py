import logging

import borgmatic.config.paths
from borgmatic.borg import environment, flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def break_lock(
    repository_path,
    config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, an
    argparse.Namespace of global arguments, and optional local and remote Borg paths, break any
    repository and cache locks leftover from Borg aborting.
    '''
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)

    full_command = (
        (local_path, 'break-lock')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    execute_command(
        full_command,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
