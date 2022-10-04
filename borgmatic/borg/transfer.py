import logging

from borgmatic.borg import environment, flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def transfer_archives(
    dry_run,
    repository,
    storage_config,
    local_borg_version,
    transfer_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a dry-run flag, a local or remote repository path, a storage config dict, the local Borg
    version, and the arguments to the transfer action, transfer archives to the given repository.
    '''
    full_command = (
        (local_path, 'transfer')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('lock-wait', storage_config.get('lock_wait', None))
        + (
            flags.make_flags(
                'match-archives', transfer_arguments.match_archives or transfer_arguments.archive
            )
        )
        + flags.make_flags_from_arguments(
            transfer_arguments,
            excludes=('repository', 'source_repository', 'archive', 'match_archives'),
        )
        + flags.make_repository_flags(repository, local_borg_version)
        + flags.make_flags('other-repo', transfer_arguments.source_repository)
        + flags.make_flags('dry-run', dry_run)
    )

    return execute_command(
        full_command,
        output_log_level=logging.WARNING,
        borg_local_path=local_path,
        extra_environment=environment.make_environment(storage_config),
    )
