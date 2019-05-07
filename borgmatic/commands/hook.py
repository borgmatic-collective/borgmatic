import logging
import subprocess


logger = logging.getLogger(__name__)


def execute_hook(commands, config_filename, description, dry_run):
    '''

    Given a list of hook commands to execute, a config filename, a hook description, and whether
    this is a dry run, run the given commands. Or, don't run them if this is a dry run.
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

    for command in commands:
        logger.debug('{}: Hook command: {}'.format(config_filename, command))
        if not dry_run:
            subprocess.check_call(command, shell=True)
