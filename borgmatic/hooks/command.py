import logging
import os
import re

from borgmatic import execute

logger = logging.getLogger(__name__)


SOFT_FAIL_EXIT_CODE = 75


def interpolate_context(config_filename, hook_description, command, context):
    '''
    Given a config filename, a hook description, a single hook command, and a dict of context
    names/values, interpolate the values by "{name}" into the command and return the result.
    '''
    for name, value in context.items():
        command = command.replace('{%s}' % name, str(value))

    for unsupported_variable in re.findall(r'{\w+}', command):
        logger.warning(
            f"{config_filename}: Variable '{unsupported_variable}' is not supported in {hook_description} hook"
        )

    return command


def execute_hook(commands, umask, config_filename, description, dry_run, **context):
    '''
    Given a list of hook commands to execute, a umask to execute with (or None), a config filename,
    a hook description, and whether this is a dry run, run the given commands. Or, don't run them
    if this is a dry run.

    The context contains optional values interpolated by name into the hook commands.

    Raise ValueError if the umask cannot be parsed.
    Raise subprocesses.CalledProcessError if an error occurs in a hook.
    '''
    if not commands:
        logger.debug('{}: No commands to run for {} hook'.format(config_filename, description))
        return

    dry_run_label = ' (dry run; not actually running hooks)' if dry_run else ''

    context['configuration_filename'] = config_filename
    commands = [
        interpolate_context(config_filename, description, command, context) for command in commands
    ]

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


def considered_soft_failure(config_filename, error):
    '''
    Given a configuration filename and an exception object, return whether the exception object
    represents a subprocess.CalledProcessError with a return code of SOFT_FAIL_EXIT_CODE. If so,
    that indicates that the error is a "soft failure", and should not result in an error.
    '''
    exit_code = getattr(error, 'returncode', None)
    if exit_code is None:
        return False

    if exit_code == SOFT_FAIL_EXIT_CODE:
        logger.info(
            '{}: Command hook exited with soft failure exit code ({}); skipping remaining actions'.format(
                config_filename, SOFT_FAIL_EXIT_CODE
            )
        )
        return True

    return False
