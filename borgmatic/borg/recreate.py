import argparse
import logging

import borgmatic.borg.environment
import borgmatic.borg.feature
import borgmatic.borg.flags
import borgmatic.borg.repo_delete
import borgmatic.config.paths
import borgmatic.execute
from borgmatic.borg.create import make_exclude_flags, write_patterns_file

logger = logging.getLogger(__name__)


def make_recreate_command(
    repository,
    config,
    patterns,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path,
    remote_path=None,
):
    '''
    Given a repository path, configuration dict, patterns, and Borg options, return a command
    list for recreating a Borg archive.
    '''
    verbosity_flags = ()
    if logger.isEnabledFor(logging.DEBUG):
        verbosity_flags = ('--debug', '--show-rc')
    elif logger.isEnabledFor(logging.INFO):
        verbosity_flags = ('--info',)

    command = [local_path, 'recreate', repository]
    command.extend(verbosity_flags)
    command.extend(global_arguments)
    command.extend(recreate_arguments)

    exclude_flags = make_exclude_flags(config)
    command.extend(exclude_flags)

    return command


def recreate_archive(
    repository,
    config,
    patterns,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Recreate a Borg archive with the given repository and configuration.
    '''
    command = make_recreate_command(
        repository,
        config,
        patterns,
        local_borg_version,
        recreate_arguments,
        global_arguments,
        local_path,
        remote_path,
    )

    patterns_file = write_patterns_file(patterns, borgmatic.config.paths.get_runtime_directory())
    if patterns_file:
        command.extend(['--patterns-from', patterns_file.name])

    borgmatic.execute.execute_command(
        command,
        output_log_level=logging.ANSWER,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        remote_path=remote_path, 
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes')
        )
