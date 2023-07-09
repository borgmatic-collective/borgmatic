import logging

import borgmatic.logger
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command, execute_command_and_capture_output

logger = logging.getLogger(__name__)


def display_repository_info(
    repository_path,
    config,
    local_borg_version,
    rinfo_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the rinfo action, and global arguments as an argparse.Namespace, display summary
    information for the Borg repository or return JSON summary information.
    '''
    borgmatic.logger.add_custom_log_levels()
    lock_wait = config.get('lock_wait', None)

    full_command = (
        (local_path,)
        + (
            ('rinfo',)
            if feature.available(feature.Feature.RINFO, local_borg_version)
            else ('info',)
        )
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not rinfo_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not rinfo_arguments.json
            else ()
        )
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('log-json', global_arguments.log_json)
        + flags.make_flags('lock-wait', lock_wait)
        + (('--json',) if rinfo_arguments.json else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    extra_environment = environment.make_environment(config)

    if rinfo_arguments.json:
        return execute_command_and_capture_output(
            full_command,
            extra_environment=extra_environment,
        )
    else:
        execute_command(
            full_command,
            output_log_level=logging.ANSWER,
            borg_local_path=local_path,
            extra_environment=extra_environment,
        )
