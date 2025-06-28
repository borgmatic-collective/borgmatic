import collections
import importlib.metadata
import json
import logging
import os
import sys
import time
from queue import Queue
from subprocess import CalledProcessError

import ruamel.yaml

import borgmatic.actions.borg
import borgmatic.actions.break_lock
import borgmatic.actions.change_passphrase
import borgmatic.actions.check
import borgmatic.actions.compact
import borgmatic.actions.config.bootstrap
import borgmatic.actions.config.generate
import borgmatic.actions.config.validate
import borgmatic.actions.create
import borgmatic.actions.delete
import borgmatic.actions.export_key
import borgmatic.actions.export_tar
import borgmatic.actions.extract
import borgmatic.actions.import_key
import borgmatic.actions.info
import borgmatic.actions.list
import borgmatic.actions.mount
import borgmatic.actions.prune
import borgmatic.actions.recreate
import borgmatic.actions.repo_create
import borgmatic.actions.repo_delete
import borgmatic.actions.repo_info
import borgmatic.actions.repo_list
import borgmatic.actions.restore
import borgmatic.actions.transfer
import borgmatic.commands.completion.bash
import borgmatic.commands.completion.fish
import borgmatic.config.load
import borgmatic.config.paths
from borgmatic.borg import umount as borg_umount
from borgmatic.borg import version as borg_version
from borgmatic.commands.arguments import parse_arguments
from borgmatic.config import checks, collect, validate
from borgmatic.hooks import command, dispatch
from borgmatic.hooks.monitoring import monitor
from borgmatic.logger import (
    DISABLED,
    Log_prefix,
    add_custom_log_levels,
    configure_delayed_logging,
    configure_logging,
    should_do_markup,
)
from borgmatic.signals import configure_signals
from borgmatic.verbosity import get_verbosity, verbosity_to_log_level

logger = logging.getLogger(__name__)


def get_skip_actions(config, arguments):
    '''
    Given a configuration dict and command-line arguments as an argparse.Namespace, return a list of
    the configured action names to skip. Omit "check" from this list though if "check --force" is
    part of the command-like arguments.
    '''
    skip_actions = config.get('skip_actions', [])

    if 'check' in arguments and arguments['check'].force:
        return [action for action in skip_actions if action != 'check']

    return skip_actions


class Monitoring_hooks:
    '''
    A Python context manager for pinging monitoring hooks for the start state before the wrapped
    code and log and finish (or failure) after the wrapped code. Also responsible for
    initializing/destroying the monitoring hooks.

    Example use as a context manager:

       with Monitoring_hooks(config_filename, config, arguments, global_arguments):
           do_stuff()
    '''

    def __init__(self, config_filename, config, arguments, global_arguments):
        '''
        Given a configuration filename, a configuration dict, command-line arguments as an
        argparse.Namespace, and global arguments as an argparse.Namespace, save relevant data points
        for use below.
        '''
        using_primary_action = {'create', 'prune', 'compact', 'check'}.intersection(arguments)
        self.config_filename = config_filename
        self.config = config
        self.dry_run = global_arguments.dry_run
        self.monitoring_log_level = verbosity_to_log_level(
            get_verbosity({config_filename: config}, 'monitoring_verbosity')
        )
        self.monitoring_hooks_are_activated = (
            using_primary_action and self.monitoring_log_level != DISABLED
        )

    def __enter__(self):
        '''
        If monitoring hooks are enabled and a primary action is in use, initialize monitoring hooks
        and ping them for the "start" state.
        '''
        if not self.monitoring_hooks_are_activated:
            return

        dispatch.call_hooks(
            'initialize_monitor',
            self.config,
            dispatch.Hook_type.MONITORING,
            self.config_filename,
            self.monitoring_log_level,
            self.dry_run,
        )

        try:
            dispatch.call_hooks(
                'ping_monitor',
                self.config,
                dispatch.Hook_type.MONITORING,
                self.config_filename,
                monitor.State.START,
                self.monitoring_log_level,
                self.dry_run,
            )
        except (OSError, CalledProcessError) as error:
            raise ValueError(f'Error pinging monitor: {error}')

    def __exit__(self, exception_type, exception, traceback):
        '''
        If monitoring hooks are enabled and a primary action is in use, ping monitoring hooks for
        the "log" state and also the "finish" or "fail" states (depending on whether there's an
        exception). Lastly, destroy monitoring hooks.
        '''
        if not self.monitoring_hooks_are_activated:
            return

        # Send logs irrespective of error.
        try:
            dispatch.call_hooks(
                'ping_monitor',
                self.config,
                dispatch.Hook_type.MONITORING,
                self.config_filename,
                monitor.State.LOG,
                self.monitoring_log_level,
                self.dry_run,
            )
        except (OSError, CalledProcessError) as error:
            raise ValueError(f'Error pinging monitor: {error}')

        try:
            dispatch.call_hooks(
                'ping_monitor',
                self.config,
                dispatch.Hook_type.MONITORING,
                self.config_filename,
                monitor.State.FAIL if exception else monitor.State.FINISH,
                self.monitoring_log_level,
                self.dry_run,
            )
        except (OSError, CalledProcessError) as error:
            # If the wrapped code errored, prefer raising that exception, as it's probably more
            # important than a monitor failing to ping.
            if exception:
                return

            raise ValueError(f'Error pinging monitor: {error}')

        dispatch.call_hooks(
            'destroy_monitor',
            self.config,
            dispatch.Hook_type.MONITORING,
            self.monitoring_log_level,
            self.dry_run,
        )


def run_configuration(config_filename, config, config_paths, arguments):
    '''
    Given a config filename, the corresponding parsed config dict, a sequence of loaded
    configuration paths, and command-line arguments as a dict from subparser name to a namespace of
    parsed arguments, execute the defined create, prune, compact, check, and/or other actions.

    Yield a combination of:

      * JSON output strings from successfully executing any actions that produce JSON
      * logging.LogRecord instances containing errors from any actions or backup hooks that fail
    '''
    global_arguments = arguments['global']

    local_path = config.get('local_path', 'borg')
    remote_path = config.get('remote_path')
    retries = config.get('retries', 0)
    retry_wait = config.get('retry_wait', 0)
    repo_queue = Queue()
    encountered_error = None
    error_repository = None
    skip_actions = get_skip_actions(config, arguments)

    if skip_actions:
        logger.debug(
            f"Skipping {'/'.join(skip_actions)} action{'s' if len(skip_actions) > 1 else ''} due to configured skip_actions"
        )

    try:
        with Monitoring_hooks(config_filename, config, arguments, global_arguments):
            with borgmatic.hooks.command.Before_after_hooks(
                command_hooks=config.get('commands'),
                before_after='configuration',
                umask=config.get('umask'),
                working_directory=borgmatic.config.paths.get_working_directory(config),
                dry_run=global_arguments.dry_run,
                action_names=arguments.keys(),
                configuration_filename=config_filename,
                log_file=config.get('log_file', ''),
            ):
                try:
                    local_borg_version = borg_version.local_borg_version(config, local_path)
                    logger.debug(f'Borg {local_borg_version}')
                except (OSError, CalledProcessError, ValueError) as error:
                    yield from log_error_records(
                        f'{config_filename}: Error getting local Borg version', error
                    )
                    raise

                for repo in config['repositories']:
                    repo_queue.put(
                        (repo, 0),
                    )

                while not repo_queue.empty():
                    repository, retry_num = repo_queue.get()

                    with Log_prefix(repository.get('label', repository['path'])):
                        logger.debug('Running actions for repository')
                        timeout = retry_num * retry_wait
                        if timeout:
                            logger.warning(f'Sleeping {timeout}s before next retry')
                            time.sleep(timeout)
                        try:
                            yield from run_actions(
                                arguments=arguments,
                                config_filename=config_filename,
                                config=config,
                                config_paths=config_paths,
                                local_path=local_path,
                                remote_path=remote_path,
                                local_borg_version=local_borg_version,
                                repository=repository,
                            )
                        except (OSError, CalledProcessError, ValueError) as error:
                            if retry_num < retries:
                                repo_queue.put(
                                    (repository, retry_num + 1),
                                )
                                tuple(  # Consume the generator so as to trigger logging.
                                    log_error_records(
                                        'Error running actions for repository',
                                        error,
                                        levelno=logging.WARNING,
                                        log_command_error_output=True,
                                    )
                                )
                                logger.warning(f'Retrying... attempt {retry_num + 1}/{retries}')
                                continue

                            if command.considered_soft_failure(error):
                                continue

                            yield from log_error_records(
                                'Error running actions for repository',
                                error,
                            )
                            encountered_error = error
                            error_repository = repository

                # Re-raise any error, so that the Monitoring_hooks context manager wrapping this
                # code can see the error and act accordingly. Do this here rather than as soon as
                # the error is encountered so that an error with one repository doesn't prevent
                # other repositories from running.
                if encountered_error:
                    raise encountered_error

    except (OSError, CalledProcessError, ValueError) as error:
        yield from log_error_records('Error running configuration')

        encountered_error = error

    if not encountered_error:
        return

    try:
        command.execute_hooks(
            command.filter_hooks(
                config.get('commands'),
                after='error',
                action_names=arguments.keys(),
                state_names=['fail'],
            ),
            config.get('umask'),
            borgmatic.config.paths.get_working_directory(config),
            global_arguments.dry_run,
            configuration_filename=config_filename,
            log_file=config.get('log_file', ''),
            repository=error_repository.get('path', '') if error_repository else '',
            repository_label=error_repository.get('label', '') if error_repository else '',
            error=encountered_error,
            output=getattr(encountered_error, 'output', ''),
        )
    except (OSError, CalledProcessError) as error:
        if command.considered_soft_failure(error):
            return

        yield from log_error_records(f'{config_filename}: Error running after error hook', error)


def run_actions(
    *,
    arguments,
    config_filename,
    config,
    config_paths,
    local_path,
    remote_path,
    local_borg_version,
    repository,
):
    '''
    Given parsed command-line arguments as an argparse.ArgumentParser instance, the configuration
    filename, a configuration dict, a sequence of loaded configuration paths, local and remote paths
    to Borg, a local Borg version string, and a repository name, run all actions from the
    command-line arguments on the given repository.

    Yield JSON output strings from executing any actions that produce JSON.

    Raise OSError or subprocess.CalledProcessError if an error occurs running a command for an
    action or a hook. Raise ValueError if the arguments or configuration passed to action are
    invalid.
    '''
    add_custom_log_levels()
    repository_path = os.path.expanduser(repository['path'])
    global_arguments = arguments['global']
    dry_run_label = ' (dry run; not making any changes)' if global_arguments.dry_run else ''
    hook_context = {
        'configuration_filename': config_filename,
        'repository_label': repository.get('label', ''),
        'log_file': config.get('log_file', ''),
        # Deprecated: For backwards compatibility with borgmatic < 1.6.0.
        'repositories': ','.join([repo['path'] for repo in config['repositories']]),
        'repository': repository_path,
    }
    skip_actions = set(get_skip_actions(config, arguments))

    with borgmatic.hooks.command.Before_after_hooks(
        command_hooks=config.get('commands'),
        before_after='repository',
        umask=config.get('umask'),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        dry_run=global_arguments.dry_run,
        action_names=arguments.keys(),
        **hook_context,
    ):
        for action_name, action_arguments in arguments.items():
            if action_name == 'global' or action_name in skip_actions:
                continue

            with borgmatic.hooks.command.Before_after_hooks(
                command_hooks=config.get('commands'),
                before_after='action',
                umask=config.get('umask'),
                working_directory=borgmatic.config.paths.get_working_directory(config),
                dry_run=global_arguments.dry_run,
                action_names=(action_name,),
                **hook_context,
            ):
                if action_name == 'repo-create':
                    borgmatic.actions.repo_create.run_repo_create(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'transfer':
                    borgmatic.actions.transfer.run_transfer(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'create':
                    yield from borgmatic.actions.create.run_create(
                        config_filename,
                        repository,
                        config,
                        config_paths,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        dry_run_label,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'recreate':
                    borgmatic.actions.recreate.run_recreate(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'prune':
                    borgmatic.actions.prune.run_prune(
                        config_filename,
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        dry_run_label,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'compact':
                    borgmatic.actions.compact.run_compact(
                        config_filename,
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        dry_run_label,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'check':
                    if checks.repository_enabled_for_checks(repository, config):
                        borgmatic.actions.check.run_check(
                            config_filename,
                            repository,
                            config,
                            local_borg_version,
                            action_arguments,
                            global_arguments,
                            local_path,
                            remote_path,
                        )
                elif action_name == 'extract':
                    borgmatic.actions.extract.run_extract(
                        config_filename,
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'export-tar':
                    borgmatic.actions.export_tar.run_export_tar(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'mount':
                    borgmatic.actions.mount.run_mount(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'restore':
                    borgmatic.actions.restore.run_restore(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'repo-list':
                    yield from borgmatic.actions.repo_list.run_repo_list(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'list':
                    yield from borgmatic.actions.list.run_list(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'repo-info':
                    yield from borgmatic.actions.repo_info.run_repo_info(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'info':
                    yield from borgmatic.actions.info.run_info(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'break-lock':
                    borgmatic.actions.break_lock.run_break_lock(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'export':
                    borgmatic.actions.export_key.run_export_key(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'import':
                    borgmatic.actions.import_key.run_import_key(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'change-passphrase':
                    borgmatic.actions.change_passphrase.run_change_passphrase(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'delete':
                    borgmatic.actions.delete.run_delete(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'repo-delete':
                    borgmatic.actions.repo_delete.run_repo_delete(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )
                elif action_name == 'borg':
                    borgmatic.actions.borg.run_borg(
                        repository,
                        config,
                        local_borg_version,
                        action_arguments,
                        global_arguments,
                        local_path,
                        remote_path,
                    )


def load_configurations(config_filenames, arguments, overrides=None, resolve_env=True):
    '''
    Given a sequence of configuration filenames, arguments as a dict from action name to
    argparse.Namespace, a sequence of configuration file override strings in the form of
    "option.suboption=value", and whether to resolve environment variables, load and validate each
    configuration file. Return the results as a tuple of: dict of configuration filename to
    corresponding parsed configuration, a sequence of paths for all loaded configuration files
    (including includes), and a sequence of logging.LogRecord instances containing any parse errors.

    Log records are returned here instead of being logged directly because logging isn't yet
    initialized at this point! (Although with the Delayed_logging_handler now in place, maybe this
    approach could change.)
    '''
    # Dict mapping from config filename to corresponding parsed config dict.
    configs = collections.OrderedDict()
    config_paths = set()
    logs = []

    # Parse and load each configuration file.
    for config_filename in config_filenames:
        logs.extend(
            [
                logging.makeLogRecord(
                    dict(
                        levelno=logging.DEBUG,
                        levelname='DEBUG',
                        msg=f'{config_filename}: Loading configuration file',
                    )
                ),
            ]
        )
        try:
            configs[config_filename], paths, parse_logs = validate.parse_configuration(
                config_filename,
                validate.schema_filename(),
                arguments,
                overrides,
                resolve_env,
            )
            config_paths.update(paths)
            logs.extend(parse_logs)
        except PermissionError:
            logs.extend(
                [
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.WARNING,
                            levelname='WARNING',
                            msg=f'{config_filename}: Insufficient permissions to read configuration file',
                        )
                    ),
                ]
            )
        except (ValueError, OSError, validate.Validation_error) as error:
            logs.extend(
                [
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.CRITICAL,
                            levelname='CRITICAL',
                            msg=f'{config_filename}: Error parsing configuration file',
                        )
                    ),
                    logging.makeLogRecord(
                        dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg=str(error))
                    ),
                ]
            )

    return (configs, sorted(config_paths), logs)


def log_record(suppress_log=False, **kwargs):
    '''
    Create a log record based on the given makeLogRecord() arguments, one of which must be
    named "levelno". Log the record (unless suppress log is set) and return it.
    '''
    record = logging.makeLogRecord(kwargs)
    if suppress_log:
        return record

    logger.handle(record)
    return record


BORG_REPOSITORY_ACCESS_ABORTED_EXIT_CODE = 62


def log_error_records(
    message, error=None, levelno=logging.CRITICAL, log_command_error_output=False
):
    '''
    Given error message text, an optional exception object, an optional log level, and whether to
    log the error output of a CalledProcessError (if any), log error summary information and also
    yield it as a series of logging.LogRecord instances.

    Note that because the logs are yielded as a generator, logs won't get logged unless you consume
    the generator output.
    '''
    level_name = logging._levelToName[levelno]

    if not error:
        yield log_record(levelno=levelno, levelname=level_name, msg=str(message))
        return

    try:
        raise error
    except CalledProcessError as error:
        yield log_record(levelno=levelno, levelname=level_name, msg=str(message))

        if error.output:
            try:
                output = error.output.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                output = error.output

            # Suppress these logs for now and save the error output for the log summary at the end.
            # Log a separate record per line, as some errors can be really verbose and overflow the
            # per-record size limits imposed by some logging backends.
            for output_line in output.splitlines():
                yield log_record(
                    levelno=levelno,
                    levelname=level_name,
                    msg=output_line,
                    suppress_log=True,
                )

        yield log_record(levelno=levelno, levelname=level_name, msg=str(error))

        if error.returncode == BORG_REPOSITORY_ACCESS_ABORTED_EXIT_CODE:
            yield log_record(
                levelno=levelno,
                levelname=level_name,
                msg='\nTo work around this, set either the "relocated_repo_access_is_ok" or "unknown_unencrypted_repo_access_is_ok" option to "true", as appropriate.',
            )
    except (ValueError, OSError) as error:
        yield log_record(levelno=levelno, levelname=level_name, msg=str(message))
        yield log_record(levelno=levelno, levelname=level_name, msg=str(error))
    except:  # noqa: E722, S110
        # Raising above only as a means of determining the error type. Swallow the exception here
        # because we don't want the exception to propagate out of this function.
        pass


def get_local_path(configs):
    '''
    Arbitrarily return the local path from the first configuration dict. Default to "borg" if not
    set.
    '''
    return next(iter(configs.values())).get('local_path', 'borg')


def collect_highlander_action_summary_logs(configs, arguments, configuration_parse_errors):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, parsed
    command-line arguments as a dict from subparser name to a parsed namespace of arguments, and
    whether any configuration files encountered errors during parsing, run a highlander action
    specified in the arguments, if any, and yield a series of logging.LogRecord instances containing
    summary information.

    A highlander action is an action that cannot coexist with other actions on the borgmatic
    command-line, and borgmatic exits after processing such an action.
    '''
    add_custom_log_levels()

    if 'bootstrap' in arguments:
        try:
            # No configuration file is needed for bootstrap.
            local_borg_version = borg_version.local_borg_version(
                {}, arguments['bootstrap'].local_path
            )
        except (OSError, CalledProcessError, ValueError) as error:
            yield from log_error_records('Error getting local Borg version', error)
            return

        try:
            borgmatic.actions.config.bootstrap.run_bootstrap(
                arguments['bootstrap'], arguments['global'], local_borg_version
            )
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.ANSWER,
                    levelname='ANSWER',
                    msg='Bootstrap successful',
                )
            )
        except (
            CalledProcessError,
            ValueError,
            OSError,
        ) as error:
            yield from log_error_records(error)

        return

    if 'generate' in arguments:
        try:
            borgmatic.actions.config.generate.run_generate(
                arguments['generate'], arguments['global']
            )
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.ANSWER,
                    levelname='ANSWER',
                    msg='Generate successful',
                )
            )
        except (
            CalledProcessError,
            ValueError,
            OSError,
        ) as error:
            yield from log_error_records(error)

        return

    if 'validate' in arguments:
        if configuration_parse_errors:
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.CRITICAL,
                    levelname='CRITICAL',
                    msg='Configuration validation failed',
                )
            )

            return

        try:
            borgmatic.actions.config.validate.run_validate(arguments['validate'], configs)

            yield logging.makeLogRecord(
                dict(
                    levelno=logging.ANSWER,
                    levelname='ANSWER',
                    msg='All configuration files are valid',
                )
            )
        except (
            CalledProcessError,
            ValueError,
            OSError,
        ) as error:
            yield from log_error_records(error)

        return


def collect_configuration_run_summary_logs(configs, config_paths, arguments, log_file_path):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, a sequence of
    loaded configuration paths, parsed command-line arguments as a dict from subparser name to a
    parsed namespace of arguments, and the path of a log file (if any), run each configuration file
    and yield a series of logging.LogRecord instances containing summary information about each run.

    As a side effect of running through these configuration files, output their JSON results, if
    any, to stdout.
    '''
    # Run cross-file validation checks.
    repository = None

    for action_name, action_arguments in arguments.items():
        if hasattr(action_arguments, 'repository'):
            repository = getattr(action_arguments, 'repository')
            break

    try:
        validate.guard_configuration_contains_repository(repository, configs)
    except ValueError as error:
        yield from log_error_records(str(error))
        return

    if not configs:
        yield from log_error_records(
            f"{' '.join(arguments['global'].config_paths)}: No valid configuration files found",
        )
        return

    try:
        seen_command_hooks = []

        for config_filename, config in configs.items():
            command_hooks = command.filter_hooks(
                tuple(
                    command_hook
                    for command_hook in config.get('commands', ())
                    if command_hook not in seen_command_hooks
                ),
                before='everything',
                action_names=arguments.keys(),
            )

            if command_hooks:
                command.execute_hooks(
                    command_hooks,
                    config.get('umask'),
                    borgmatic.config.paths.get_working_directory(config),
                    arguments['global'].dry_run,
                    configuration_filename=config_filename,
                    log_file=log_file_path or '',
                )
                seen_command_hooks += list(command_hooks)
    except (CalledProcessError, ValueError, OSError) as error:
        yield from log_error_records('Error running before everything hook', error)
        return

    # Execute the actions corresponding to each configuration file.
    json_results = []
    encountered_error = False

    for config_filename, config in configs.items():
        with Log_prefix(config_filename):
            results = list(run_configuration(config_filename, config, config_paths, arguments))

            error_logs = tuple(
                result for result in results if isinstance(result, logging.LogRecord)
            )

            if error_logs:
                encountered_error = True
                yield from log_error_records('An error occurred')
                yield from error_logs
            else:
                yield logging.makeLogRecord(
                    dict(
                        levelno=logging.INFO,
                        levelname='INFO',
                        msg=f'{config_filename}: Successfully ran configuration file',
                    )
                )
                if results:
                    json_results.extend(results)

    if 'umount' in arguments:
        logger.info(f"Unmounting mount point {arguments['umount'].mount_point}")
        try:
            borg_umount.unmount_archive(
                config,
                mount_point=arguments['umount'].mount_point,
                local_path=get_local_path(configs),
            )
        except (CalledProcessError, OSError) as error:
            encountered_error = True
            yield from log_error_records('Error unmounting mount point', error)

    if json_results:
        sys.stdout.write(json.dumps(json_results))

    try:
        seen_command_hooks = []

        for config_filename, config in configs.items():
            command_hooks = command.filter_hooks(
                tuple(
                    command_hook
                    for command_hook in config.get('commands', ())
                    if command_hook not in seen_command_hooks
                ),
                after='everything',
                action_names=arguments.keys(),
                state_names=['fail' if encountered_error else 'finish'],
            )

            if command_hooks:
                command.execute_hooks(
                    command_hooks,
                    config.get('umask'),
                    borgmatic.config.paths.get_working_directory(config),
                    arguments['global'].dry_run,
                    configuration_filename=config_filename,
                    log_file=log_file_path or '',
                )
                seen_command_hooks += list(command_hooks)
    except (CalledProcessError, ValueError, OSError) as error:
        yield from log_error_records('Error running after everything hook', error)


def exit_with_help_link():  # pragma: no cover
    '''
    Display a link to get help and exit with an error code.
    '''
    logger.critical('')
    logger.critical('Need some help? https://torsion.org/borgmatic/#issues')
    sys.exit(1)


def check_and_show_help_on_no_args(configs):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, check if the
    borgmatic command is run without any arguments. If the configuration option "default_actions" is
    set to False, show the help message. Otherwise, trigger the default backup behavior.
    '''
    if len(sys.argv) == 1:  # No arguments provided
        default_actions = any(config.get('default_actions', True) for config in configs.values())
        if not default_actions:
            parse_arguments('--help')
            sys.exit(0)


def get_singular_option_value(configs, option_name):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, return the value
    of the given option from the configuration files or None if it's not set.

    Log and exit if there are conflicting values for the option across the configuration files.
    '''
    distinct_values = {
        value
        for config in configs.values()
        for value in (config.get(option_name),)
        if value is not None
    }

    if len(distinct_values) > 1:
        configure_logging(logging.CRITICAL)
        joined_values = ', '.join(str(value) for value in distinct_values)
        logger.critical(
            f'The {option_name} option has conflicting values across configuration files: {joined_values}'
        )
        exit_with_help_link()

    try:
        return tuple(distinct_values)[0]
    except IndexError:
        return None


def main(extra_summary_logs=[]):  # pragma: no cover
    configure_signals()
    configure_delayed_logging()
    schema_filename = validate.schema_filename()

    try:
        schema = borgmatic.config.load.load_configuration(schema_filename)
    except (ruamel.yaml.error.YAMLError, RecursionError) as error:
        configure_logging(logging.CRITICAL)
        logger.critical(error)
        exit_with_help_link()

    try:
        arguments = parse_arguments(schema, *sys.argv[1:])
    except ValueError as error:
        configure_logging(logging.CRITICAL)
        logger.critical(error)
        exit_with_help_link()
    except SystemExit as error:
        if error.code == 0:
            raise error
        configure_logging(logging.CRITICAL)
        logger.critical(f"Error parsing arguments: {' '.join(sys.argv)}")
        exit_with_help_link()

    global_arguments = arguments['global']
    if global_arguments.version:
        print(importlib.metadata.version('borgmatic'))
        sys.exit(0)
    if global_arguments.bash_completion:
        print(borgmatic.commands.completion.bash.bash_completion())
        sys.exit(0)
    if global_arguments.fish_completion:
        print(borgmatic.commands.completion.fish.fish_completion())
        sys.exit(0)

    config_filenames = tuple(collect.collect_config_filenames(global_arguments.config_paths))
    configs, config_paths, parse_logs = load_configurations(
        config_filenames,
        arguments,
        global_arguments.overrides,
        resolve_env=global_arguments.resolve_env and not arguments.get('validate'),
    )

    # Use the helper function to check and show help on no arguments, passing the preloaded configs
    check_and_show_help_on_no_args(configs)

    configuration_parse_errors = (
        (max(log.levelno for log in parse_logs) >= logging.CRITICAL) if parse_logs else False
    )

    any_json_flags = any(
        getattr(sub_arguments, 'json', False) for sub_arguments in arguments.values()
    )
    log_file_path = get_singular_option_value(configs, 'log_file')

    try:
        configure_logging(
            verbosity_to_log_level(get_verbosity(configs, 'verbosity')),
            verbosity_to_log_level(get_verbosity(configs, 'syslog_verbosity')),
            verbosity_to_log_level(get_verbosity(configs, 'log_file_verbosity')),
            verbosity_to_log_level(get_verbosity(configs, 'monitoring_verbosity')),
            log_file_path,
            get_singular_option_value(configs, 'log_file_format'),
            color_enabled=should_do_markup(configs, any_json_flags),
        )
    except (FileNotFoundError, PermissionError) as error:
        configure_logging(logging.CRITICAL)
        logger.critical(f'Error configuring logging: {error}')
        exit_with_help_link()

    summary_logs = (
        extra_summary_logs
        + parse_logs
        + (
            list(
                collect_highlander_action_summary_logs(
                    configs, arguments, configuration_parse_errors
                )
            )
            or list(
                collect_configuration_run_summary_logs(
                    configs, config_paths, arguments, log_file_path
                )
            )
        )
    )
    summary_logs_max_level = max(log.levelno for log in summary_logs)

    for message in ('', 'summary:'):
        log_record(
            levelno=summary_logs_max_level,
            levelname=logging.getLevelName(summary_logs_max_level),
            msg=message,
        )

    for log in summary_logs:
        logger.handle(log)

    if summary_logs_max_level >= logging.CRITICAL:
        exit_with_help_link()
