import logging
import shlex

import borgmatic.commands.arguments
import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, flags
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


BORG_SUBCOMMANDS_WITH_SUBCOMMANDS = {'key', 'debug'}


def run_arbitrary_borg(
    repository_path,
    config,
    local_borg_version,
    options,
    archive=None,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, a
    sequence of arbitrary command-line Borg options, and an optional archive name, run an arbitrary
    Borg command, passing in REPOSITORY and ARCHIVE environment variables for optional use in the
    command.
    '''
    borgmatic.logger.add_custom_log_levels()
    lock_wait = config.get('lock_wait', None)

    try:
        options = options[1:] if options[0] == '--' else options

        # Borg commands like "key" have a sub-command ("export", etc.) that must follow it.
        command_options_start_index = 2 if options[0] in BORG_SUBCOMMANDS_WITH_SUBCOMMANDS else 1
        borg_command = tuple(options[:command_options_start_index])
        command_options = tuple(options[command_options_start_index:])

        if borg_command and borg_command[0] in borgmatic.commands.arguments.ACTION_ALIASES.keys():
            logger.warning(
                f"Borg's {borg_command[0]} subcommand is supported natively by borgmatic. Try this instead: borgmatic {borg_command[0]}"
            )
    except IndexError:
        borg_command = ()
        command_options = ()

    full_command = (
        (local_path,)
        + borg_command
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('lock-wait', lock_wait)
        + command_options
    )

    return execute_command(
        tuple(shlex.quote(part) for part in full_command),
        output_file=DO_NOT_CAPTURE,
        shell=True,  # noqa: S604
        environment=dict(
            (environment.make_environment(config) or {}),
            **{
                'BORG_REPO': repository_path,
                'ARCHIVE': archive if archive else '',
            },
        ),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
