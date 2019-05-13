import subprocess

from borgmatic.logger import get_logger

logger = get_logger(__name__)


def execute_command(full_command, capture_output=False):
    '''
    Execute the given command (a sequence of command/argument strings). If capture output is True,
    then return the command's output as a string.
    '''
    logger.debug(' '.join(full_command))

    if capture_output:
        output = subprocess.check_output(full_command)
        return output.decode() if output is not None else None
    else:
        subprocess.check_call(full_command)
