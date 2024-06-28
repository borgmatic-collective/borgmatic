import logging

import borgmatic.borg.environment
import borgmatic.borg.feature
import borgmatic.borg.flags
import borgmatic.execute

logger = logging.getLogger(__name__)


def make_rdelete_command(
    repository,
    config,
    local_borg_version,
    rdelete_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Given a local or remote repository dict, a configuration dict, the local Borg version, the
    arguments to the rdelete action as an argparse.Namespace, and global arguments, return a command
    as a tuple to rdelete the entire repository.
    '''
    return (
        (local_path,)
        + (
            ('rdelete',)
            if borgmatic.borg.feature.available(
                borgmatic.borg.feature.Feature.RDELETE, local_borg_version
            )
            else ('delete',)
        )
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + borgmatic.borg.flags.make_flags('remote-path', remote_path)
        + borgmatic.borg.flags.make_flags('log-json', global_arguments.log_json)
        + borgmatic.borg.flags.make_flags('lock-wait', config.get('lock_wait'))
        + borgmatic.borg.flags.make_flags('list', rdelete_arguments.list_archives)
        + (
            (('--force',) + (('--force',) if rdelete_arguments.force >= 2 else ()))
            if rdelete_arguments.force
            else ()
        )
        + borgmatic.borg.flags.make_flags_from_arguments(
            rdelete_arguments, excludes=('list_archives', 'force', 'repository')
        )
        + borgmatic.borg.flags.make_repository_flags(repository['path'], local_borg_version)
    )


def delete_repository(
    repository,
    config,
    local_borg_version,
    rdelete_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository dict, a configuration dict, the local Borg version, the
    arguments to the rdelete action as an argparse.Namespace, global arguments as an
    argparse.Namespace, and local and remote Borg paths, rdelete the entire repository.
    '''
    borgmatic.logger.add_custom_log_levels()

    command = make_rdelete_command(
        repository,
        config,
        local_borg_version,
        rdelete_arguments,
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
            if rdelete_arguments.force or rdelete_arguments.cache_only
            else borgmatic.execute.DO_NOT_CAPTURE
        ),
        extra_environment=borgmatic.borg.environment.make_environment(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
