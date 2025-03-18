import logging

import borgmatic.borg.environment
import borgmatic.config.paths
import borgmatic.execute
from borgmatic.borg.create import make_exclude_flags
from borgmatic.borg.flags import make_flags_from_arguments, make_repository_archive_flags

logger = logging.getLogger(__name__)


def make_recreate_command(
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

    Returns the recreate command as a tuple of strings ready for execution.
    '''
    verbosity_flags = (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ()) + (
        ('--info',) if logger.isEnabledFor(logging.INFO) else ()
    )

    # handle both the recreate and global arguments
    recreate_flags = make_flags_from_arguments(
        recreate_arguments, excludes=('repository', 'archive')
    )
    global_flags = make_flags_from_arguments(global_arguments)

    repo_archive_flags = make_repository_archive_flags(repository, archive, local_borg_version)
    exclude_flags = make_exclude_flags(config)

    return (
        (local_path, 'recreate')
        + repo_archive_flags
        + verbosity_flags
        + global_flags
        + recreate_flags
        + exclude_flags
    )


def recreate_archive(
    repository,
    archive,
    config,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, an archive name, a configuration dict,
    the local Borg version string, an argparse.Namespace of recreate arguments,
    an argparse.Namespace of global arguments, optional local and remote Borg paths.

    Executes the recreate command with the given arguments.
    '''
    command = make_recreate_command(
        repository,
        archive,
        config,
        local_borg_version,
        recreate_arguments,
        global_arguments,
        local_path,
        remote_path,
    )

    borgmatic.execute.execute_command(
        command,
        output_log_level=logging.ANSWER,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        remote_path=remote_path,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
