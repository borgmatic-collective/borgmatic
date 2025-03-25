import logging

import borgmatic.borg.environment
import borgmatic.config.paths
import borgmatic.execute
from borgmatic.borg.create import make_exclude_flags, make_list_filter_flags, write_patterns_file
from borgmatic.borg.flags import make_repository_archive_flags

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
    patterns=None,
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

    # Write patterns to a temporary file and use that file with --patterns-from.
    patterns_file = write_patterns_file(
        patterns, borgmatic.config.paths.get_working_directory(config)
    )

    recreate_cmd = (
        (local_path, 'recreate')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--path', recreate_arguments.path) if recreate_arguments.path else ())
        + (('--log-json',) if global_arguments.log_json else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--patterns-from', patterns_file.name) if patterns_file else ())
        + (
            (
                '--list',
                '--filter',
                make_list_filter_flags(local_borg_version, global_arguments.dry_run),
            )
            if recreate_arguments.list
            else ()
        )
        + exclude_flags
        + repo_archive_arg
    )

    if global_arguments.dry_run:
        logger.info('Skipping the archive recreation (dry run)')
        return

    borgmatic.execute.execute_command(
        full_command=recreate_cmd,
        output_log_level=logging.INFO,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
