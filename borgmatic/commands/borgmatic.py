import collections
import importlib.metadata
import json
import logging
import os
import sys
import time
from queue import Queue
from subprocess import CalledProcessError

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
import borgmatic.actions.info
import borgmatic.actions.list
import borgmatic.actions.mount
import borgmatic.actions.prune
import borgmatic.actions.repo_create
import borgmatic.actions.repo_delete
import borgmatic.actions.repo_info
import borgmatic.actions.repo_list
import borgmatic.actions.restore
import borgmatic.actions.transfer
import borgmatic.commands.completion.bash
import borgmatic.commands.completion.fish
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
from borgmatic.verbosity import verbosity_to_log_level

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
    encountered_error = None
    error_repository = ''
    using_primary_action = {'create', 'prune', 'compact', 'check'}.intersection(arguments)
    monitoring_log_level = verbosity_to_log_level(global_arguments.monitoring_verbosity)
    monitoring_hooks_are_activated = using_primary_action and monitoring_log_level != DISABLED
    skip_actions = get_skip_actions(config, arguments)

    if skip_actions:
        logger.debug(
            f"Skipping {'/'.join(skip_actions)} action{'s' if len(skip_actions) > 1 else ''} due to configured skip_actions"
        )

    try:
        local_borg_version = borg_version.local_borg_version(config, local_path)
        logger.debug(f'Borg {local_borg_version}')
    except (OSError, CalledProcessError, ValueError) as error:
        yield from log_error_records(f'{config_filename}: Error getting local Borg version', error)
        return

    try:
        if monitoring_hooks_are_activated:
            dispatch.call_hooks(
                'initialize_monitor',
                config,
                dispatch.Hook_type.MONITORING,
                config_filename,
                monitoring_log_level,
                global_arguments.dry_run,
            )

            dispatch.call_hooks(
                'ping_monitor',
                config,
                dispatch.Hook_type.MONITORING,
                config_filename,
                monitor.State.START,
                monitoring_log_level,
                global_arguments.dry_run,
            )
    except (OSError, CalledProcessError) as error:
        if command.considered_soft_failure(error):
            return

        encountered_error = error
        yield from log_error_records(f'{config_filename}: Error pinging monitor', error)

    if not encountered_error:
        repo_queue = Queue()
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
                    error_repository = repository['path']

    try:
        if monitoring_hooks_are_activated:
            # Send logs irrespective of error.
            dispatch.call_hooks(
                'ping_monitor',
                config,
                dispatch.Hook_type.MONITORING,
                config_filename,
                monitor.State.LOG,
                monitoring_log_level,
                global_arguments.dry_run,
            )
    except (OSError, CalledProcessError) as error:
        if not command.considered_soft_failure(error):
            encountered_error = error
            yield from log_error_records('Error pinging monitor', error)

    if not encountered_error:
        try:
            if monitoring_hooks_are_activated:
                dispatch.call_hooks(
                    'ping_monitor',
                    config,
                    dispatch.Hook_type.MONITORING,
                    config_filename,
                    monitor.State.FINISH,
                    monitoring_log_level,
                    global_arguments.dry_run,
                )
                dispatch.call_hooks(
                    'destroy_monitor',
                    config,
                    dispatch.Hook_type.MONITORING,
                    monitoring_log_level,
                    global_arguments.dry_run,
                )
        except (OSError, CalledProcessError) as error:
            if command.considered_soft_failure(error):
                return

            encountered_error = error
            yield from log_error_records(f'{config_filename}: Error pinging monitor', error)

    if encountered_error and using_primary_action:
        try:
            command.execute_hook(
                config.get('on_error'),
                config.get('umask'),
                config_filename,
                'on-error',
                global_arguments.dry_run,
                repository=error_repository,
                error=encountered_error,
                output=getattr(encountered_error, 'output', ''),
            )
            dispatch.call_hooks(
                'ping_monitor',
                config,
                dispatch.Hook_type.MONITORING,
                config_filename,
                monitor.State.FAIL,
                monitoring_log_level,
                global_arguments.dry_run,
            )
            dispatch.call_hooks(
                'destroy_monitor',
                config,
                dispatch.Hook_type.MONITORING,
                monitoring_log_level,
                global_arguments.dry_run,
            )
        except (OSError, CalledProcessError) as error:
            if command.considered_soft_failure(error):
                return

            yield from log_error_records(f'{config_filename}: Error running on-error hook', error)


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
        'repository_label': repository.get('label', ''),
        'log_file': global_arguments.log_file if global_arguments.log_file else '',
        # Deprecated: For backwards compatibility with borgmatic < 1.6.0.
        'repositories': ','.join([repo['path'] for repo in config['repositories']]),
        'repository': repository_path,
    }
    skip_actions = set(get_skip_actions(config, arguments))

    command.execute_hook(
        config.get('before_actions'),
        config.get('umask'),
        config_filename,
        'pre-actions',
        global_arguments.dry_run,
        **hook_context,
    )

    for action_name, action_arguments in arguments.items():
        if action_name == 'repo-create' and action_name not in skip_actions:
            borgmatic.actions.repo_create.run_repo_create(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'transfer' and action_name not in skip_actions:
            borgmatic.actions.transfer.run_transfer(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'create' and action_name not in skip_actions:
            yield from borgmatic.actions.create.run_create(
                config_filename,
                repository,
                config,
                config_paths,
                hook_context,
                local_borg_version,
                action_arguments,
                global_arguments,
                dry_run_label,
                local_path,
                remote_path,
            )
        elif action_name == 'prune' and action_name not in skip_actions:
            borgmatic.actions.prune.run_prune(
                config_filename,
                repository,
                config,
                hook_context,
                local_borg_version,
                action_arguments,
                global_arguments,
                dry_run_label,
                local_path,
                remote_path,
            )
        elif action_name == 'compact' and action_name not in skip_actions:
            borgmatic.actions.compact.run_compact(
                config_filename,
                repository,
                config,
                hook_context,
                local_borg_version,
                action_arguments,
                global_arguments,
                dry_run_label,
                local_path,
                remote_path,
            )
        elif action_name == 'check' and action_name not in skip_actions:
            if checks.repository_enabled_for_checks(repository, config):
                borgmatic.actions.check.run_check(
                    config_filename,
                    repository,
                    config,
                    hook_context,
                    local_borg_version,
                    action_arguments,
                    global_arguments,
                    local_path,
                    remote_path,
                )
        elif action_name == 'extract' and action_name not in skip_actions:
            borgmatic.actions.extract.run_extract(
                config_filename,
                repository,
                config,
                hook_context,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'export-tar' and action_name not in skip_actions:
            borgmatic.actions.export_tar.run_export_tar(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'mount' and action_name not in skip_actions:
            borgmatic.actions.mount.run_mount(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'restore' and action_name not in skip_actions:
            borgmatic.actions.restore.run_restore(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'repo-list' and action_name not in skip_actions:
            yield from borgmatic.actions.repo_list.run_repo_list(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'list' and action_name not in skip_actions:
            yield from borgmatic.actions.list.run_list(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'repo-info' and action_name not in skip_actions:
            yield from borgmatic.actions.repo_info.run_repo_info(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'info' and action_name not in skip_actions:
            yield from borgmatic.actions.info.run_info(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'break-lock' and action_name not in skip_actions:
            borgmatic.actions.break_lock.run_break_lock(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'export' and action_name not in skip_actions:
            borgmatic.actions.export_key.run_export_key(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'change-passphrase' and action_name not in skip_actions:
            borgmatic.actions.change_passphrase.run_change_passphrase(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'delete' and action_name not in skip_actions:
            borgmatic.actions.delete.run_delete(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'repo-delete' and action_name not in skip_actions:
            borgmatic.actions.repo_delete.run_repo_delete(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        elif action_name == 'borg' and action_name not in skip_actions:
            borgmatic.actions.borg.run_borg(
                repository,
                config,
                local_borg_version,
                action_arguments,
                global_arguments,
                local_path,
                remote_path,
            )

    command.execute_hook(
        config.get('after_actions'),
        config.get('umask'),
        config_filename,
        'post-actions',
        global_arguments.dry_run,
        **hook_context,
    )


def load_configurations(config_filenames, overrides=None, resolve_env=True):
    '''
    Given a sequence of configuration filenames, a sequence of configuration file override strings
    in the form of "option.suboption=value", and whether to resolve environment variables, load and
    validate each configuration file. Return the results as a tuple of: dict of configuration
    filename to corresponding parsed configuration, a sequence of paths for all loaded configuration
    files (including includes), and a sequence of logging.LogRecord instances containing any parse
    errors.

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
    except:  # noqa: E722
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


def collect_configuration_run_summary_logs(configs, config_paths, arguments):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, a sequence of
    loaded configuration paths, and parsed command-line arguments as a dict from subparser name to a
    parsed namespace of arguments, run each configuration file and yield a series of
    logging.LogRecord instances containing summary information about each run.

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

    if 'create' in arguments:
        try:
            for config_filename, config in configs.items():
                command.execute_hook(
                    config.get('before_everything'),
                    config.get('umask'),
                    config_filename,
                    'pre-everything',
                    arguments['global'].dry_run,
                )
        except (CalledProcessError, ValueError, OSError) as error:
            yield from log_error_records('Error running pre-everything hook', error)
            return

    # Execute the actions corresponding to each configuration file.
    json_results = []

    for config_filename, config in configs.items():
        with Log_prefix(config_filename):
            results = list(run_configuration(config_filename, config, config_paths, arguments))
            error_logs = tuple(
                result for result in results if isinstance(result, logging.LogRecord)
            )

            if error_logs:
                yield from log_error_records('An error occurred')
                yield from error_logs
            else:
                yield logging.makeLogRecord(
                    dict(
                        levelno=logging.INFO,
                        levelname='INFO',
                        msg='Successfully ran configuration file',
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
            yield from log_error_records('Error unmounting mount point', error)

    if json_results:
        sys.stdout.write(json.dumps(json_results))

    if 'create' in arguments:
        try:
            for config_filename, config in configs.items():
                command.execute_hook(
                    config.get('after_everything'),
                    config.get('umask'),
                    config_filename,
                    'post-everything',
                    arguments['global'].dry_run,
                )
        except (CalledProcessError, ValueError, OSError) as error:
            yield from log_error_records('Error running post-everything hook', error)


def exit_with_help_link():  # pragma: no cover
    '''
    Display a link to get help and exit with an error code.
    '''
    logger.critical('')
    logger.critical('Need some help? https://torsion.org/borgmatic/#issues')
    sys.exit(1)


def main(extra_summary_logs=[]):  # pragma: no cover
    configure_signals()
    configure_delayed_logging()

    try:
        arguments = parse_arguments(*sys.argv[1:])
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

    validate = bool('validate' in arguments)
    config_filenames = tuple(collect.collect_config_filenames(global_arguments.config_paths))
    configs, config_paths, parse_logs = load_configurations(
        config_filenames,
        global_arguments.overrides,
        resolve_env=global_arguments.resolve_env and not validate,
    )
    configuration_parse_errors = (
        (max(log.levelno for log in parse_logs) >= logging.CRITICAL) if parse_logs else False
    )

    any_json_flags = any(
        getattr(sub_arguments, 'json', False) for sub_arguments in arguments.values()
    )
    color_enabled = should_do_markup(global_arguments.no_color or any_json_flags, configs)

    try:
        configure_logging(
            verbosity_to_log_level(global_arguments.verbosity),
            verbosity_to_log_level(global_arguments.syslog_verbosity),
            verbosity_to_log_level(global_arguments.log_file_verbosity),
            verbosity_to_log_level(global_arguments.monitoring_verbosity),
            global_arguments.log_file,
            global_arguments.log_file_format,
            color_enabled=color_enabled,
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
            or list(collect_configuration_run_summary_logs(configs, config_paths, arguments))
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
