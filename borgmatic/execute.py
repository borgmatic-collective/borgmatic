import logging
import subprocess

from borgmatic.logger import get_logger

logger = get_logger(__name__)


def execute_and_log_output(full_command, output_log_level, shell):
    process = subprocess.Popen(
        full_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell
    )

    while process.poll() is None:
        line = process.stdout.readline().rstrip().decode()
        if not line:
            continue

        if line.startswith('borg: error:'):
            logger.error(line)
        else:
            logger.log(output_log_level, line)

    remaining_output = process.stdout.read().rstrip().decode()
    if remaining_output:  # pragma: no cover
        logger.log(output_log_level, remaining_output)

    exit_code = process.poll()
    if exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, full_command)


def execute_command(full_command, output_log_level=logging.INFO, shell=False):
    '''
    Execute the given command (a sequence of command/argument strings) and log its output at the
    given log level. If output log level is None, instead capture and return the output. If
    shell is True, execute the command within a shell.
    '''
    logger.debug(' '.join(full_command))

    if output_log_level is None:
        output = subprocess.check_output(full_command, shell=shell)
        return output.decode() if output is not None else None
    else:
        execute_and_log_output(full_command, output_log_level, shell=shell)
