import logging

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, flags
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def transfer_archives(
    dry_run,
    repository_path,
    config,
    local_borg_version,
    transfer_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a dry-run flag, a local or remote repository path, a configuration dict, the local Borg
    version, the arguments to the transfer action, and global arguments as an argparse.Namespace
    instance, transfer archives to the given repository.
    '''
    borgmatic.logger.add_custom_log_levels()

    full_command = (
        (local_path, 'transfer')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('log-json', global_arguments.log_json)
        + flags.make_flags('lock-wait', config.get('lock_wait', None))
        + (
            flags.make_flags_from_arguments(
                transfer_arguments,
                excludes=('repository', 'source_repository', 'archive', 'match_archives'),
            )
            or (
                flags.make_match_archives_flags(
                    transfer_arguments.match_archives
                    or transfer_arguments.archive
                    or config.get('match_archives'),
                    config.get('archive_name_format'),
                    local_borg_version,
                )
            )
        )
        + flags.make_repository_flags(repository_path, local_borg_version)
        + flags.make_flags('other-repo', transfer_arguments.source_repository)
        + flags.make_flags('dry-run', dry_run)
    )

    return execute_command(
        full_command,
        output_log_level=logging.ANSWER,
        output_file=DO_NOT_CAPTURE if transfer_arguments.progress else None,
        extra_environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
