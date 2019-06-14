import logging
import os

from borgmatic import execute
from borgmatic.logger import get_logger

logger = get_logger(__name__)


def execute_hook(commands, umask, config_filename, description, dry_run):
    '''
    Given a list of hook commands to execute, a umask to execute with (or None), a config filename,
    a hook description, and whether this is a dry run, run the given commands. Or, don't run them
    if this is a dry run.

    Raise ValueError if the umask cannot be parsed.
    '''
    if not commands:
        logger.debug('{}: No commands to run for {} hook'.format(config_filename, description))
        return

    dry_run_label = ' (dry run; not actually running hooks)' if dry_run else ''

    if len(commands) == 1:
        logger.info(
            '{}: Running command for {} hook{}'.format(config_filename, description, dry_run_label)
        )
    else:
        logger.info(
            '{}: Running {} commands for {} hook{}'.format(
                config_filename, len(commands), description, dry_run_label
            )
        )

    if umask:
        parsed_umask = int(str(umask), 8)
        logger.debug('{}: Set hook umask to {}'.format(config_filename, oct(parsed_umask)))
        original_umask = os.umask(parsed_umask)
    else:
        original_umask = None

    try:
        for command in commands:
            if not dry_run:
                execute.execute_command(
                    [command],
                    output_log_level=logging.ERROR
                    if description == 'on-error'
                    else logging.WARNING,
                    shell=True,
                )
    finally:
        if original_umask:
            os.umask(original_umask)
