import subprocess

from borgmatic.logger import get_logger

logger = get_logger(__name__)


def execute_and_log_output(full_command, output_as_warning=False):
    process = subprocess.Popen(full_command, stdout=None, stderr=subprocess.PIPE)

    while process.poll() is None:
        line = process.stderr.readline().rstrip().decode()
        if line.startswith('borg: error:'):
            logger.error(line)
        elif output_as_warning:
            logger.warning(line)
        else:
            logger.info(line)

    remaining_output = process.stderr.read().rstrip().decode()
    if remaining_output:
        logger.info(remaining_output)

    exit_code = process.poll()
    if exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, full_command)


def execute_command(full_command, capture_output=False, output_as_warning=False):
    '''
    Execute the given command (a sequence of command/argument strings). If capture output is True,
    then return the command's output as a string.
    '''
    logger.debug(' '.join(full_command))

    if capture_output:
        output = subprocess.check_output(full_command)
        return output.decode() if output is not None else None
    else:
        execute_and_log_output(full_command, output_as_warning)
