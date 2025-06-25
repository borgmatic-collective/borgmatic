import argparse
import json
import logging

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command, execute_command_and_capture_output

logger = logging.getLogger(__name__)


def resolve_archive_name(
    repository_path,
    archive,
    config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, an archive name, a configuration dict, the local Borg
    version, global arguments as an argparse.Namespace, a local Borg path, and a remote Borg path,
    return the archive name. But if the archive name is "latest", then instead introspect the
    repository for the latest archive and return its name.

    Raise ValueError if "latest" is given but there are no archives in the repository.
    '''
    if archive != 'latest':
        return archive

    latest_archive = get_latest_archive(
        repository_path,
        config,
        local_borg_version,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
    )

    return latest_archive['name']


def get_latest_archive(
    repository_path,
    config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
    consider_checkpoints=False,
):
    '''
    Returns a dict with information about the latest archive of a repository.

    Raises ValueError if there are no archives in the repository.
    '''

    full_command = (
        (
            local_path,
            (
                'repo-list'
                if feature.available(feature.Feature.REPO_LIST, local_borg_version)
                else 'list'
            ),
        )
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('umask', config.get('umask'))
        + flags.make_flags('log-json', config.get('log_json'))
        + flags.make_flags('lock-wait', config.get('lock_wait'))
        + flags.make_flags('consider-checkpoints', consider_checkpoints)
        + flags.make_flags('last', 1)
        + ('--json',)
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    json_output = execute_command_and_capture_output(
        full_command,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    archives = json.loads(json_output)['archives']

    try:
        latest_archive = archives[-1]
    except IndexError:
        raise ValueError('No archives found in the repository')

    logger.debug(f'Latest archive is {latest_archive["name"]}')

    return latest_archive


MAKE_FLAGS_EXCLUDES = ('repository', 'prefix', 'match_archives')


def make_repo_list_command(
    repository_path,
    config,
    local_borg_version,
    repo_list_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the repo_list action, global arguments as an argparse.Namespace instance, and local and
    remote Borg paths, return a command as a tuple to list archives with a repository.
    '''
    return (
        (
            local_path,
            (
                'repo-list'
                if feature.available(feature.Feature.REPO_LIST, local_borg_version)
                else 'list'
            ),
        )
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not repo_list_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not repo_list_arguments.json
            else ()
        )
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('umask', config.get('umask'))
        + flags.make_flags('log-json', config.get('log_json'))
        + flags.make_flags('lock-wait', config.get('lock_wait'))
        + (
            (
                flags.make_flags('match-archives', f'sh:{repo_list_arguments.prefix}*')
                if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version)
                else flags.make_flags('glob-archives', f'{repo_list_arguments.prefix}*')
            )
            if repo_list_arguments.prefix
            else (
                flags.make_match_archives_flags(
                    config.get('match_archives'),
                    config.get('archive_name_format'),
                    local_borg_version,
                )
            )
        )
        + flags.make_flags_from_arguments(repo_list_arguments, excludes=MAKE_FLAGS_EXCLUDES)
        + flags.make_repository_flags(repository_path, local_borg_version)
    )


def list_repository(
    repository_path,
    config,
    local_borg_version,
    repo_list_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the list action, global arguments as an argparse.Namespace instance, and local and
    remote Borg paths, display the output of listing Borg archives in the given repository (or
    return JSON output).
    '''
    borgmatic.logger.add_custom_log_levels()

    main_command = make_repo_list_command(
        repository_path,
        config,
        local_borg_version,
        repo_list_arguments,
        global_arguments,
        local_path,
        remote_path,
    )
    json_command = make_repo_list_command(
        repository_path,
        config,
        local_borg_version,
        argparse.Namespace(**dict(repo_list_arguments.__dict__, json=True)),
        global_arguments,
        local_path,
        remote_path,
    )
    working_directory = borgmatic.config.paths.get_working_directory(config)
    borg_exit_codes = config.get('borg_exit_codes')

    json_listing = execute_command_and_capture_output(
        json_command,
        environment=environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=borg_exit_codes,
    )

    if repo_list_arguments.json:
        return json_listing

    flags.warn_for_aggressive_archive_flags(json_command, json_listing)

    execute_command(
        main_command,
        output_log_level=logging.ANSWER,
        environment=environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=borg_exit_codes,
    )
