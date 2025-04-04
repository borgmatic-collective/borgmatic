import argparse
import logging

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command, execute_command_and_capture_output

logger = logging.getLogger(__name__)


def make_info_command(
    repository_path,
    config,
    local_borg_version,
    info_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the info action as an argparse.Namespace, and global arguments, return a command
    as a tuple to display summary information for archives in the repository.
    '''
    return (
        (local_path, 'info')
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not info_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not info_arguments.json
            else ()
        )
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('umask', config.get('umask'))
        + flags.make_flags('log-json', config.get('log_json'))
        + flags.make_flags('lock-wait', config.get('lock_wait'))
        + (
            (
                flags.make_flags('match-archives', f'sh:{info_arguments.prefix}*')
                if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version)
                else flags.make_flags('glob-archives', f'{info_arguments.prefix}*')
            )
            if info_arguments.prefix
            else (
                flags.make_match_archives_flags(
                    info_arguments.archive or config.get('match_archives'),
                    config.get('archive_name_format'),
                    local_borg_version,
                )
            )
        )
        + flags.make_flags_from_arguments(
            info_arguments, excludes=('repository', 'archive', 'prefix', 'match_archives')
        )
        + flags.make_repository_flags(repository_path, local_borg_version)
    )


def display_archives_info(
    repository_path,
    config,
    local_borg_version,
    info_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the info action as an argparse.Namespace, and global arguments, display summary
    information for Borg archives in the repository or return JSON summary information.
    '''
    borgmatic.logger.add_custom_log_levels()

    main_command = make_info_command(
        repository_path,
        config,
        local_borg_version,
        info_arguments,
        global_arguments,
        local_path,
        remote_path,
    )
    json_command = make_info_command(
        repository_path,
        config,
        local_borg_version,
        argparse.Namespace(**dict(info_arguments.__dict__, json=True)),
        global_arguments,
        local_path,
        remote_path,
    )
    borg_exit_codes = config.get('borg_exit_codes')
    working_directory = borgmatic.config.paths.get_working_directory(config)

    json_info = execute_command_and_capture_output(
        json_command,
        environment=environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=borg_exit_codes,
    )

    if info_arguments.json:
        return json_info

    flags.warn_for_aggressive_archive_flags(json_command, json_info)

    execute_command(
        main_command,
        output_log_level=logging.ANSWER,
        environment=environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=borg_exit_codes,
    )
