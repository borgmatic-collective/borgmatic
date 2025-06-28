import functools
import logging
import os
import re
import shlex
import subprocess
import sys

import borgmatic.execute
import borgmatic.logger

logger = logging.getLogger(__name__)


SOFT_FAIL_EXIT_CODE = 75
BORG_PLACEHOLDERS = {
    '{hostname}',
    '{fqdn}',
    '{reverse-fqdn}',
    '{now}',
    '{utcnow}',
    '{unixtime}',
    '{user}',
    '{pid}',
    '{borgversion}',
    '{borgmajor}',
    '{borgminor}',
    '{borgpatch}',
}


def interpolate_context(hook_description, command, context):
    '''
    Given a config filename, a hook description, a single hook command, and a dict of context
    names/values, interpolate the values by "{name}" into the command and return the result.
    '''
    for name, value in context.items():
        command = command.replace(f'{{{name}}}', shlex.quote(str(value)))

    for unsupported_variable in re.findall(r'\{\w+\}', command):
        # Warn about variables unknown to borgmatic, but don't warn if the variable name happens to
        # be a Borg placeholder, as Borg should hopefully consume it.
        if unsupported_variable not in BORG_PLACEHOLDERS:
            logger.warning(
                f'Variable "{unsupported_variable}" is not supported in the {hook_description} hook'
            )

    return command


def make_environment(current_environment, sys_module=sys):
    '''
    Given the existing system environment as a map from environment variable name to value, return a
    copy of it, augmented with any extra environment variables that should be used when running
    command hooks.
    '''
    environment = dict(current_environment)

    # Detect whether we're running within a PyInstaller bundle. If so, set or clear LD_LIBRARY_PATH
    # based on the value of LD_LIBRARY_PATH_ORIG. This prevents library version information errors.
    if getattr(sys_module, 'frozen', False) and hasattr(sys_module, '_MEIPASS'):
        environment['LD_LIBRARY_PATH'] = environment.get('LD_LIBRARY_PATH_ORIG', '')

    return environment


def filter_hooks(command_hooks, before=None, after=None, action_names=None, state_names=None):
    '''
    Given a sequence of command hook dicts from configuration and one or more filters (before name,
    after name, a sequence of action names, and/or a sequence of execution result state names),
    filter down the command hooks to just the ones that match the given filters.
    '''
    return tuple(
        hook_config
        for hook_config in command_hooks or ()
        for config_action_names in (hook_config.get('when'),)
        for config_state_names in (hook_config.get('states'),)
        if before is None or hook_config.get('before') == before
        if after is None or hook_config.get('after') == after
        if action_names is None
        or config_action_names is None
        or set(config_action_names or ()).intersection(set(action_names))
        if state_names is None
        or config_state_names is None
        or set(config_state_names or ()).intersection(set(state_names))
    )


def execute_hooks(command_hooks, umask, working_directory, dry_run, **context):
    '''
    Given a sequence of command hook dicts from configuration, a umask to execute with (or None), a
    working directory to execute with, and whether this is a dry run, run the commands for each
    hook. Or don't run them if this is a dry run.

    The context contains optional values interpolated by name into the hook commands.

    Raise ValueError if the umask cannot be parsed or a hook is invalid.
    Raise subprocesses.CalledProcessError if an error occurs in a hook.
    '''
    borgmatic.logger.add_custom_log_levels()

    dry_run_label = ' (dry run; not actually running hooks)' if dry_run else ''

    for hook_config in command_hooks:
        commands = hook_config.get('run')
        when_description = (
            f"{'/'.join(hook_config.get('when'))} " if hook_config.get('when') else ''
        )

        if 'before' in hook_config:
            description = f'before {when_description}{hook_config.get("before")}'
        elif 'after' in hook_config:
            description = f'after {when_description}{hook_config.get("after")}'
        else:
            raise ValueError(f'Invalid hook configuration: {hook_config}')

        if not commands:
            logger.debug(f'No commands to run for {description} hook')
            continue

        commands = [interpolate_context(description, command, context) for command in commands]

        if len(commands) == 1:
            logger.info(f'Running {description} command hook{dry_run_label}')
        else:
            logger.info(
                f'Running {len(commands)} commands for {description} hook{dry_run_label}',
            )

        if umask:
            parsed_umask = int(str(umask), 8)
            logger.debug(f'Setting hook umask to {oct(parsed_umask)}')
            original_umask = os.umask(parsed_umask)
        else:
            original_umask = None

        try:
            for command in commands:
                if dry_run:
                    continue

                borgmatic.execute.execute_command(
                    [command],
                    output_log_level=(
                        logging.ERROR if hook_config.get('after') == 'error' else logging.ANSWER
                    ),
                    shell=True,  # noqa: S604
                    environment=make_environment(os.environ),
                    working_directory=working_directory,
                )
        finally:
            if original_umask:
                os.umask(original_umask)


class Before_after_hooks:
    '''
    A Python context manager for executing command hooks both before and after the wrapped code.

    Example use as a context manager:

       with borgmatic.hooks.command.Before_after_hooks(
           command_hooks=config.get('commands'),
           before_after='do_stuff',
           umask=config.get('umask'),
           dry_run=dry_run,
           action_names=['create'],
       ):
            do()
            some()
            stuff()

    With that context manager in place, "before" command hooks execute before the wrapped code runs,
    and "after" command hooks execute after the wrapped code completes.
    '''

    def __init__(
        self,
        command_hooks,
        before_after,
        umask,
        working_directory,
        dry_run,
        action_names=None,
        **context,
    ):
        '''
        Given a sequence of command hook configuration dicts, the before/after name, a umask to run
        commands with, a working directory to run commands with, a dry run flag, a sequence of
        action names, and any context for the executed commands, save those data points for use
        below.
        '''
        self.command_hooks = command_hooks
        self.before_after = before_after
        self.umask = umask
        self.working_directory = working_directory
        self.dry_run = dry_run
        self.action_names = action_names
        self.context = context

    def __enter__(self):
        '''
        Run the configured "before" command hooks that match the initialized data points.
        '''
        try:
            execute_hooks(
                borgmatic.hooks.command.filter_hooks(
                    self.command_hooks,
                    before=self.before_after,
                    action_names=self.action_names,
                ),
                self.umask,
                self.working_directory,
                self.dry_run,
                **self.context,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            if considered_soft_failure(error):
                raise

            # Trigger the after hook manually, since raising here will prevent it from being run
            # otherwise.
            self.__exit__(exception_type=type(error), exception=error, traceback=None)

            raise ValueError(f'Error running before {self.before_after} hook: {error}')

    def __exit__(self, exception_type, exception, traceback):
        '''
        Run the configured "after" command hooks that match the initialized data points.
        '''
        try:
            execute_hooks(
                borgmatic.hooks.command.filter_hooks(
                    self.command_hooks,
                    after=self.before_after,
                    action_names=self.action_names,
                    state_names=['fail' if exception_type else 'finish'],
                ),
                self.umask,
                self.working_directory,
                self.dry_run,
                **self.context,
            )
        except (OSError, subprocess.CalledProcessError) as error:
            if considered_soft_failure(error):
                raise

            raise ValueError(f'Error running after {self.before_after} hook: {error}')


@functools.cache
def considered_soft_failure(error):
    '''
    Given a configuration filename and an exception object, return whether the exception object
    represents a subprocess.CalledProcessError with a return code of SOFT_FAIL_EXIT_CODE. If so,
    that indicates that the error is a "soft failure", and should not result in an error.

    The results of this function are cached so that it can be called multiple times without logging
    multiple times.
    '''
    exit_code = getattr(error, 'returncode', None)
    if exit_code is None:
        return False

    if exit_code == SOFT_FAIL_EXIT_CODE:
        logger.info(
            f'Command hook exited with soft failure exit code ({SOFT_FAIL_EXIT_CODE}); skipping remaining repository actions',
        )
        return True

    return False
