import logging

from borgmatic.borg import environment
from borgmatic.borg.flags import make_flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


REPOSITORYLESS_BORG_COMMANDS = {'serve', None}
BORG_COMMANDS_WITH_SUBCOMMANDS = {'key', 'debug'}
BORG_SUBCOMMANDS_WITHOUT_REPOSITORY = (('debug', 'info'), ('debug', 'convert-profile'))


def run_arbitrary_borg(
    repository, storage_config, options, archive=None, local_path='borg', remote_path=None
):
    '''
    Given a local or remote repository path, a storage config dict, a sequence of arbitrary
    command-line Borg options, and an optional archive name, run an arbitrary Borg command on the
    given repository/archive.
    '''
    lock_wait = storage_config.get('lock_wait', None)

    try:
        options = options[1:] if options[0] == '--' else options

        # Borg commands like "key" have a sub-command ("export", etc.) that must follow it.
        command_options_start_index = 2 if options[0] in BORG_COMMANDS_WITH_SUBCOMMANDS else 1
        borg_command = tuple(options[:command_options_start_index])
        command_options = tuple(options[command_options_start_index:])
    except IndexError:
        borg_command = ()
        command_options = ()

    if borg_command in BORG_SUBCOMMANDS_WITHOUT_REPOSITORY:
        repository_archive = None
    else:
        repository_archive = (
            '::'.join((repository, archive)) if repository and archive else repository
        )

    full_command = (
        (local_path,)
        + borg_command
        + ((repository_archive,) if borg_command and repository_archive else ())
        + command_options
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + make_flags('remote-path', remote_path)
        + make_flags('lock-wait', lock_wait)
    )

    return execute_command(
        full_command,
        output_log_level=logging.WARNING,
        borg_local_path=local_path,
        extra_environment=environment.make_environment(storage_config),
    )
