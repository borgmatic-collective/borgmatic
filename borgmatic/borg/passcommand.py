import functools
import logging
import shlex

import borgmatic.config.paths
import borgmatic.execute

logger = logging.getLogger(__name__)


@functools.cache
def run_passcommand(passcommand, passphrase_configured, working_directory):
    '''
    Run the given passcommand using the given working directory and return the passphrase produced
    by the command. But bail first if a passphrase is already configured; this mimics Borg's
    behavior.

    Cache the results so that the passcommand only needs to run—and potentially prompt the user—once
    per borgmatic invocation.
    '''
    if passcommand and passphrase_configured:
        logger.warning(
            'Ignoring the "encryption_passcommand" option because "encryption_passphrase" is set'
        )
        return None

    return borgmatic.execute.execute_command_and_capture_output(
        shlex.split(passcommand),
        working_directory=working_directory,
    )


def get_passphrase_from_passcommand(config):
    '''
    Given the configuration dict, call the configured passcommand to produce and return an
    encryption passphrase. In effect, we're doing an end-run around Borg by invoking its passcommand
    ourselves. This allows us to pass the resulting passphrase to multiple different Borg
    invocations without the user having to be prompted multiple times.

    If no passcommand is configured, then return None.
    '''
    passcommand = config.get('encryption_passcommand')

    if not passcommand:
        return None

    passphrase = config.get('encryption_passphrase')
    working_directory = borgmatic.config.paths.get_working_directory(config)

    return run_passcommand(passcommand, bool(passphrase), working_directory)
