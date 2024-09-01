import logging

import borgmatic.execute
import borgmatic.logger
from borgmatic.borg import environment, flags

logger = logging.getLogger(__name__)


def change_passphrase(
    repository_path,
    config,
    local_borg_version,
    change_passphrase_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, change
    passphrase arguments, and optional local and remote Borg paths, change the repository passphrase
    based on an interactive prompt.
    '''
    borgmatic.logger.add_custom_log_levels()
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)

    full_command = (
        (local_path, 'key', 'change-passphrase')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if global_arguments.log_json else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_repository_flags(
            repository_path,
            local_borg_version,
        )
    )

    if global_arguments.dry_run:
        logger.info(f'{repository_path}: Skipping change password (dry run)')
        return

    borgmatic.execute.execute_command(
        full_command,
        output_file=borgmatic.execute.DO_NOT_CAPTURE,
        output_log_level=logging.ANSWER,
        extra_environment=environment.make_environment(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    logger.answer(
        f"{repository_path}: Don't forget to update your encryption_passphrase option (if needed)"
    )
