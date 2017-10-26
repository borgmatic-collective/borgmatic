import logging
import subprocess


logger = logging.getLogger(__name__)


def execute_hook(commands, config_filename, description):
    if not commands:
        logger.debug('{}: No commands to run for {} hook'.format(config_filename, description))
        return

    if len(commands) == 1:
        logger.info('{}: Running command for {} hook'.format(config_filename, description))
    else:
        logger.info('{}: Running {} commands for {} hook'.format(config_filename, len(commands), description))

    for command in commands:
        logger.debug('{}: Hook command: {}'.format(config_filename, command))
        subprocess.check_call(command, shell=True)
