import logging

import borgmatic.borg.environment
import borgmatic.config.paths
import borgmatic.execute
from borgmatic.borg.create import make_exclude_flags
from borgmatic.borg.flags import make_flags_from_arguments, make_repository_archive_flags

logger = logging.getLogger(__name__)


def recreate_archive(
    repository,
    archive,
    config,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path,
    remote_path=None,
):
    '''
    Given a local or remote repository path, an archive name, a configuration dict,
    the local Borg version string, an argparse.Namespace of recreate arguments,
    an argparse.Namespace of global arguments, optional local and remote Borg paths.

    Executes the recreate command with the given arguments.
    '''
    lock_wait = config.get('lock_wait', None)

    repo_archive_arg = make_repository_archive_flags(repository, archive, local_borg_version)
    exclude_flags = make_exclude_flags(config)
    # handle path from recreate_arguments
    path_flag = ('--path', recreate_arguments.path) if recreate_arguments.path else ()


    recreate_cmd = (
        (local_path, 'recreate')
        + (('--remote-path', remote_path) if remote_path else ())
        + repo_archive_arg
        + path_flag
        + (('--log-json',) if global_arguments.log_json else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc', '--list') if logger.isEnabledFor(logging.DEBUG) else ())
        + exclude_flags
    )

    if global_arguments.dry_run:
        logger.info('Skipping the archive recreation (dry run)')
        return

    borgmatic.execute.execute_command(
        recreate_cmd,
        output_log_level=logging.ANSWER,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        remote_path=remote_path,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
