import argparse
import logging

import borgmatic.borg.environment
import borgmatic.borg.feature
import borgmatic.borg.flags
import borgmatic.borg.repo_delete
import borgmatic.config.paths
import borgmatic.execute

logger = logging.getLogger(__name__)


def make_delete_command(
    repository,
    config,
    local_borg_version,
    delete_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Given a local or remote repository dict, a configuration dict, the local Borg version, the
    arguments to the delete action as an argparse.Namespace, and global arguments, return a command
    as a tuple to delete archives from the repository.
    '''
    return (
        (local_path, 'delete')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + borgmatic.borg.flags.make_flags('dry-run', global_arguments.dry_run)
        + borgmatic.borg.flags.make_flags('remote-path', remote_path)
        + borgmatic.borg.flags.make_flags('umask', config.get('umask'))
        + borgmatic.borg.flags.make_flags('log-json', config.get('log_json'))
        + borgmatic.borg.flags.make_flags('lock-wait', config.get('lock_wait'))
        + borgmatic.borg.flags.make_flags('list', config.get('list_details'))
        + (
            (('--force',) + (('--force',) if delete_arguments.force >= 2 else ()))
            if delete_arguments.force
            else ()
        )
        # Ignore match_archives and archive_name_format options from configuration, so the user has
        # to be explicit on the command-line about the archives they want to delete.
        + borgmatic.borg.flags.make_match_archives_flags(
            delete_arguments.match_archives or delete_arguments.archive,
            archive_name_format=None,
            local_borg_version=local_borg_version,
            default_archive_name_format='*',
        )
        + (('--stats',) if config.get('statistics') else ())
        + borgmatic.borg.flags.make_flags_from_arguments(
            delete_arguments,
            excludes=(
                'list_details',
                'statistics',
                'force',
                'match_archives',
                'archive',
                'repository',
            ),
        )
        + borgmatic.borg.flags.make_repository_flags(repository['path'], local_borg_version)
    )


ARCHIVE_RELATED_ARGUMENT_NAMES = (
    'archive',
    'match_archives',
    'first',
    'last',
    'oldest',
    'newest',
    'older',
    'newer',
)


def delete_archives(
    repository,
    config,
    local_borg_version,
    delete_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository dict, a configuration dict, the local Borg version, the
    arguments to the delete action as an argparse.Namespace, global arguments as an
    argparse.Namespace, and local and remote Borg paths, delete the selected archives from the
    repository. If no archives are selected, then delete the entire repository.
    '''
    borgmatic.logger.add_custom_log_levels()

    if not any(
        getattr(delete_arguments, argument_name, None)
        for argument_name in ARCHIVE_RELATED_ARGUMENT_NAMES
    ):
        if borgmatic.borg.feature.available(
            borgmatic.borg.feature.Feature.REPO_DELETE, local_borg_version
        ):
            logger.warning(
                'Deleting an entire repository with the delete action is deprecated when using Borg 2.x+. Use the repo-delete action instead.'
            )

        repo_delete_arguments = argparse.Namespace(
            repository=repository['path'],
            list_details=delete_arguments.list_details,
            force=delete_arguments.force,
            cache_only=delete_arguments.cache_only,
            keep_security_info=delete_arguments.keep_security_info,
        )
        borgmatic.borg.repo_delete.delete_repository(
            repository,
            config,
            local_borg_version,
            repo_delete_arguments,
            global_arguments,
            local_path,
            remote_path,
        )

        return

    command = make_delete_command(
        repository,
        config,
        local_borg_version,
        delete_arguments,
        global_arguments,
        local_path,
        remote_path,
    )

    borgmatic.execute.execute_command(
        command,
        output_log_level=logging.ANSWER,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
