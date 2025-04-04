import logging

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command, execute_command_and_capture_output

logger = logging.getLogger(__name__)


def display_repository_info(
    repository_path,
    config,
    local_borg_version,
    repo_info_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the repo_info action, and global arguments as an argparse.Namespace, display summary
    information for the Borg repository or return JSON summary information.
    '''
    borgmatic.logger.add_custom_log_levels()
    lock_wait = config.get('lock_wait', None)

    full_command = (
        (local_path,)
        + (
            ('repo-info',)
            if feature.available(feature.Feature.REPO_INFO, local_borg_version)
            else ('info',)
        )
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not repo_info_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not repo_info_arguments.json
            else ()
        )
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('umask', config.get('umask'))
        + flags.make_flags('log-json', config.get('log_json'))
        + flags.make_flags('lock-wait', lock_wait)
        + (('--json',) if repo_info_arguments.json else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    working_directory = borgmatic.config.paths.get_working_directory(config)
    borg_exit_codes = config.get('borg_exit_codes')

    if repo_info_arguments.json:
        return execute_command_and_capture_output(
            full_command,
            environment=environment.make_environment(config),
            working_directory=working_directory,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
    else:
        execute_command(
            full_command,
            output_log_level=logging.ANSWER,
            environment=environment.make_environment(config),
            working_directory=working_directory,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
