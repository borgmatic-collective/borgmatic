import logging

import borgmatic.borg.environment
import borgmatic.borg.feature
import borgmatic.borg.flags
import borgmatic.config.paths
import borgmatic.execute

logger = logging.getLogger(__name__)


def make_repo_delete_command(
    repository,
    config,
    local_borg_version,
    repo_delete_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Given a local or remote repository dict, a configuration dict, the local Borg version, the
    arguments to the repo_delete action as an argparse.Namespace, and global arguments, return a command
    as a tuple to repo_delete the entire repository.
    '''
    return (
        (local_path,)
        + (
            ('repo-delete',)
            if borgmatic.borg.feature.available(
                borgmatic.borg.feature.Feature.REPO_DELETE, local_borg_version
            )
            else ('delete',)
        )
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + borgmatic.borg.flags.make_flags('dry-run', global_arguments.dry_run)
        + borgmatic.borg.flags.make_flags('remote-path', remote_path)
        + borgmatic.borg.flags.make_flags('umask', config.get('umask'))
        + borgmatic.borg.flags.make_flags('log-json', config.get('log_json'))
        + borgmatic.borg.flags.make_flags('lock-wait', config.get('lock_wait'))
        + borgmatic.borg.flags.make_flags('list', config.get('list_details'))
        + (
            (('--force',) + (('--force',) if repo_delete_arguments.force >= 2 else ()))
            if repo_delete_arguments.force
            else ()
        )
        + borgmatic.borg.flags.make_flags_from_arguments(
            repo_delete_arguments, excludes=('list_details', 'force', 'repository')
        )
        + borgmatic.borg.flags.make_repository_flags(repository['path'], local_borg_version)
    )


def delete_repository(
    repository,
    config,
    local_borg_version,
    repo_delete_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository dict, a configuration dict, the local Borg version, the
    arguments to the repo_delete action as an argparse.Namespace, global arguments as an
    argparse.Namespace, and local and remote Borg paths, repo_delete the entire repository.
    '''
    borgmatic.logger.add_custom_log_levels()

    command = make_repo_delete_command(
        repository,
        config,
        local_borg_version,
        repo_delete_arguments,
        global_arguments,
        local_path,
        remote_path,
    )

    borgmatic.execute.execute_command(
        command,
        output_log_level=logging.ANSWER,
        # Don't capture output when Borg is expected to prompt for interactive confirmation, or the
        # prompt won't work.
        output_file=(
            None
            if repo_delete_arguments.force or repo_delete_arguments.cache_only
            else borgmatic.execute.DO_NOT_CAPTURE
        ),
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
