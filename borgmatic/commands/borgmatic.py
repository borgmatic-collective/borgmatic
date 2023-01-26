import collections
import json
import logging
import os
import sys
import time
from queue import Queue
from subprocess import CalledProcessError

import colorama
import pkg_resources

import borgmatic.actions.borg
import borgmatic.actions.break_lock
import borgmatic.actions.check
import borgmatic.actions.compact
import borgmatic.actions.create
import borgmatic.actions.export_tar
import borgmatic.actions.extract
import borgmatic.actions.info
import borgmatic.actions.list
import borgmatic.actions.mount
import borgmatic.actions.prune
import borgmatic.actions.rcreate
import borgmatic.actions.restore
import borgmatic.actions.rinfo
import borgmatic.actions.rlist
import borgmatic.actions.transfer
import borgmatic.commands.completion
from borgmatic.borg import umount as borg_umount
from borgmatic.borg import version as borg_version
from borgmatic.commands.arguments import parse_arguments
from borgmatic.config import checks, collect, convert, validate
from borgmatic.hooks import command, dispatch, monitor
from borgmatic.logger import add_custom_log_levels, configure_logging, should_do_markup
from borgmatic.signals import configure_signals
from borgmatic.verbosity import verbosity_to_log_level

logger = logging.getLogger(__name__)

LEGACY_CONFIG_PATH = '/etc/borgmatic/config'


def run_configuration(config_filename, config, arguments):
    '''
    Given a config filename, the corresponding parsed config dict, and command-line arguments as a
    dict from subparser name to a namespace of parsed arguments, execute the defined prune, compact,
    create, check, and/or other actions.

    Yield a combination of:

      * JSON output strings from successfully executing any actions that produce JSON
      * logging.LogRecord instances containing errors from any actions or backup hooks that fail
    '''
    (location, storage, retention, consistency, hooks) = (
        config.get(section_name, {})
        for section_name in ('location', 'storage', 'retention', 'consistency', 'hooks')
    )
    global_arguments = arguments['global']

    local_path = location.get('local_path', 'borg')
    remote_path = location.get('remote_path')
    retries = storage.get('retries', 0)
    retry_wait = storage.get('retry_wait', 0)
    encountered_error = None
    error_repository = ''
    using_primary_action = {'prune', 'compact', 'create', 'check'}.intersection(arguments)
    monitoring_log_level = verbosity_to_log_level(global_arguments.monitoring_verbosity)

    try:
        local_borg_version = borg_version.local_borg_version(storage, local_path)
    except (OSError, CalledProcessError, ValueError) as error:
        yield from log_error_records(
            '{}: Error getting local Borg version'.format(config_filename), error
        )
        return

    try:
        if using_primary_action:
            dispatch.call_hooks(
                'initialize_monitor',
                hooks,
                config_filename,
                monitor.MONITOR_HOOK_NAMES,
                monitoring_log_level,
                global_arguments.dry_run,
            )
        if using_primary_action:
            dispatch.call_hooks(
                'ping_monitor',
                hooks,
                config_filename,
                monitor.MONITOR_HOOK_NAMES,
                monitor.State.START,
                monitoring_log_level,
                global_arguments.dry_run,
            )
    except (OSError, CalledProcessError) as error:
        if command.considered_soft_failure(config_filename, error):
            return

        encountered_error = error
        yield from log_error_records('{}: Error pinging monitor'.format(config_filename), error)

    if not encountered_error:
        repo_queue = Queue()
        for repo in location['repositories']:
            repo_queue.put((repo, 0),)

        while not repo_queue.empty():
            repository_path, retry_num = repo_queue.get()
            timeout = retry_num * retry_wait
            if timeout:
                logger.warning(f'{config_filename}: Sleeping {timeout}s before next retry')
                time.sleep(timeout)
            try:
                yield from run_actions(
                    arguments=arguments,
                    config_filename=config_filename,
                    location=location,
                    storage=storage,
                    retention=retention,
                    consistency=consistency,
                    hooks=hooks,
                    local_path=local_path,
                    remote_path=remote_path,
                    local_borg_version=local_borg_version,
                    repository_path=repository_path,
                )
            except (OSError, CalledProcessError, ValueError) as error:
                if retry_num < retries:
                    repo_queue.put((repository_path, retry_num + 1),)
                    tuple(  # Consume the generator so as to trigger logging.
                        log_error_records(
                            '{}: Error running actions for repository'.format(repository_path),
                            error,
                            levelno=logging.WARNING,
                            log_command_error_output=True,
                        )
                    )
                    logger.warning(
                        f'{config_filename}: Retrying... attempt {retry_num + 1}/{retries}'
                    )
                    continue

                if command.considered_soft_failure(config_filename, error):
                    return

                yield from log_error_records(
                    '{}: Error running actions for repository'.format(repository_path), error
                )
                encountered_error = error
                error_repository = repository_path

    if not encountered_error:
        try:
            if using_primary_action:
                dispatch.call_hooks(
                    'ping_monitor',
                    hooks,
                    config_filename,
                    monitor.MONITOR_HOOK_NAMES,
                    monitor.State.FINISH,
                    monitoring_log_level,
                    global_arguments.dry_run,
                )
                dispatch.call_hooks(
                    'destroy_monitor',
                    hooks,
                    config_filename,
                    monitor.MONITOR_HOOK_NAMES,
                    monitoring_log_level,
                    global_arguments.dry_run,
                )
        except (OSError, CalledProcessError) as error:
            if command.considered_soft_failure(config_filename, error):
                return

            encountered_error = error
            yield from log_error_records('{}: Error pinging monitor'.format(config_filename), error)

    if encountered_error and using_primary_action:
        try:
            command.execute_hook(
                hooks.get('on_error'),
                hooks.get('umask'),
                config_filename,
                'on-error',
                global_arguments.dry_run,
                repository=error_repository,
                error=encountered_error,
                output=getattr(encountered_error, 'output', ''),
            )
            dispatch.call_hooks(
                'ping_monitor',
                hooks,
                config_filename,
                monitor.MONITOR_HOOK_NAMES,
                monitor.State.FAIL,
                monitoring_log_level,
                global_arguments.dry_run,
            )
            dispatch.call_hooks(
                'destroy_monitor',
                hooks,
                config_filename,
                monitor.MONITOR_HOOK_NAMES,
                monitoring_log_level,
                global_arguments.dry_run,
            )
        except (OSError, CalledProcessError) as error:
            if command.considered_soft_failure(config_filename, error):
                return

            yield from log_error_records(
                '{}: Error running on-error hook'.format(config_filename), error
            )


def run_actions(
    *,
    arguments,
    config_filename,
    location,
    storage,
    retention,
    consistency,
    hooks,
    local_path,
    remote_path,
    local_borg_version,
    repository_path,
):
    '''
    Given parsed command-line arguments as an argparse.ArgumentParser instance, the configuration
    filename, several different configuration dicts, local and remote paths to Borg, a local Borg
    version string, and a repository name, run all actions from the command-line arguments on the
    given repository.

    Yield JSON output strings from executing any actions that produce JSON.

    Raise OSError or subprocess.CalledProcessError if an error occurs running a command for an
    action or a hook. Raise ValueError if the arguments or configuration passed to action are
    invalid.
    '''
    add_custom_log_levels()
    repository = os.path.expanduser(repository_path)
    global_arguments = arguments['global']
    dry_run_label = ' (dry run; not making any changes)' if global_arguments.dry_run else ''
    hook_context = {
        'repository': repository_path,
        # Deprecated: For backwards compatibility with borgmatic < 1.6.0.
        'repositories': ','.join(location['repositories']),
    }

    command.execute_hook(
        hooks.get('before_actions'),
        hooks.get('umask'),
        config_filename,
        'pre-actions',
        global_arguments.dry_run,
        **hook_context,
    )

    if 'rcreate' in arguments:
        borgmatic.actions.rcreate.run_rcreate(
            repository,
            storage,
            local_borg_version,
            arguments['rcreate'],
            global_arguments,
            local_path,
            remote_path,
        )
    if 'transfer' in arguments:
        borgmatic.actions.transfer.run_transfer(
            repository,
            storage,
            local_borg_version,
            arguments['transfer'],
            global_arguments,
            local_path,
            remote_path,
        )
    if 'prune' in arguments:
        borgmatic.actions.prune.run_prune(
            config_filename,
            repository,
            storage,
            retention,
            hooks,
            hook_context,
            local_borg_version,
            arguments['prune'],
            global_arguments,
            dry_run_label,
            local_path,
            remote_path,
        )
    if 'compact' in arguments:
        borgmatic.actions.compact.run_compact(
            config_filename,
            repository,
            storage,
            retention,
            hooks,
            hook_context,
            local_borg_version,
            arguments['compact'],
            global_arguments,
            dry_run_label,
            local_path,
            remote_path,
        )
    if 'create' in arguments:
        yield from borgmatic.actions.create.run_create(
            config_filename,
            repository,
            location,
            storage,
            hooks,
            hook_context,
            local_borg_version,
            arguments['create'],
            global_arguments,
            dry_run_label,
            local_path,
            remote_path,
        )
    if 'check' in arguments and checks.repository_enabled_for_checks(repository, consistency):
        borgmatic.actions.check.run_check(
            config_filename,
            repository,
            location,
            storage,
            consistency,
            hooks,
            hook_context,
            local_borg_version,
            arguments['check'],
            global_arguments,
            local_path,
            remote_path,
        )
    if 'extract' in arguments:
        borgmatic.actions.extract.run_extract(
            config_filename,
            repository,
            location,
            storage,
            hooks,
            hook_context,
            local_borg_version,
            arguments['extract'],
            global_arguments,
            local_path,
            remote_path,
        )
    if 'export-tar' in arguments:
        borgmatic.actions.export_tar.run_export_tar(
            repository,
            storage,
            local_borg_version,
            arguments['export-tar'],
            global_arguments,
            local_path,
            remote_path,
        )
    if 'mount' in arguments:
        borgmatic.actions.mount.run_mount(
            repository, storage, local_borg_version, arguments['mount'], local_path, remote_path,
        )
    if 'restore' in arguments:
        borgmatic.actions.restore.run_restore(
            repository,
            location,
            storage,
            hooks,
            local_borg_version,
            arguments['restore'],
            global_arguments,
            local_path,
            remote_path,
        )
    if 'rlist' in arguments:
        yield from borgmatic.actions.rlist.run_rlist(
            repository, storage, local_borg_version, arguments['rlist'], local_path, remote_path,
        )
    if 'list' in arguments:
        yield from borgmatic.actions.list.run_list(
            repository, storage, local_borg_version, arguments['list'], local_path, remote_path,
        )
    if 'rinfo' in arguments:
        yield from borgmatic.actions.rinfo.run_rinfo(
            repository, storage, local_borg_version, arguments['rinfo'], local_path, remote_path,
        )
    if 'info' in arguments:
        yield from borgmatic.actions.info.run_info(
            repository, storage, local_borg_version, arguments['info'], local_path, remote_path,
        )
    if 'break-lock' in arguments:
        borgmatic.actions.break_lock.run_break_lock(
            repository,
            storage,
            local_borg_version,
            arguments['break-lock'],
            local_path,
            remote_path,
        )
    if 'borg' in arguments:
        borgmatic.actions.borg.run_borg(
            repository, storage, local_borg_version, arguments['borg'], local_path, remote_path,
        )

    command.execute_hook(
        hooks.get('after_actions'),
        hooks.get('umask'),
        config_filename,
        'post-actions',
        global_arguments.dry_run,
        **hook_context,
    )


def load_configurations(config_filenames, overrides=None, resolve_env=True):
    '''
    Given a sequence of configuration filenames, load and validate each configuration file. Return
    the results as a tuple of: dict of configuration filename to corresponding parsed configuration,
    and sequence of logging.LogRecord instances containing any parse errors.
    '''
    # Dict mapping from config filename to corresponding parsed config dict.
    configs = collections.OrderedDict()
    logs = []

    # Parse and load each configuration file.
    for config_filename in config_filenames:
        try:
            configs[config_filename], parse_logs = validate.parse_configuration(
                config_filename, validate.schema_filename(), overrides, resolve_env
            )
            logs.extend(parse_logs)
        except PermissionError:
            logs.extend(
                [
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.WARNING,
                            levelname='WARNING',
                            msg='{}: Insufficient permissions to read configuration file'.format(
                                config_filename
                            ),
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
                            msg='{}: Error parsing configuration file'.format(config_filename),
                        )
                    ),
                    logging.makeLogRecord(
                        dict(levelno=logging.CRITICAL, levelname='CRITICAL', msg=error)
                    ),
                ]
            )

    return (configs, logs)


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
        yield log_record(levelno=levelno, levelname=level_name, msg=message)
        return

    try:
        raise error
    except CalledProcessError as error:
        yield log_record(levelno=levelno, levelname=level_name, msg=message)
        if error.output:
            # Suppress these logs for now and save full error output for the log summary at the end.
            yield log_record(
                levelno=levelno,
                levelname=level_name,
                msg=error.output,
                suppress_log=not log_command_error_output,
            )
        yield log_record(levelno=levelno, levelname=level_name, msg=error)
    except (ValueError, OSError) as error:
        yield log_record(levelno=levelno, levelname=level_name, msg=message)
        yield log_record(levelno=levelno, levelname=level_name, msg=error)
    except:  # noqa: E722
        # Raising above only as a means of determining the error type. Swallow the exception here
        # because we don't want the exception to propagate out of this function.
        pass


def get_local_path(configs):
    '''
    Arbitrarily return the local path from the first configuration dict. Default to "borg" if not
    set.
    '''
    return next(iter(configs.values())).get('location', {}).get('local_path', 'borg')


def collect_configuration_run_summary_logs(configs, arguments):
    '''
    Given a dict of configuration filename to corresponding parsed configuration, and parsed
    command-line arguments as a dict from subparser name to a parsed namespace of arguments, run
    each configuration file and yield a series of logging.LogRecord instances containing summary
    information about each run.

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
        if 'extract' in arguments or 'mount' in arguments:
            validate.guard_single_repository_selected(repository, configs)

        validate.guard_configuration_contains_repository(repository, configs)
    except ValueError as error:
        yield from log_error_records(str(error))
        return

    if not configs:
        yield from log_error_records(
            '{}: No valid configuration files found'.format(
                ' '.join(arguments['global'].config_paths)
            )
        )
        return

    if 'create' in arguments:
        try:
            for config_filename, config in configs.items():
                hooks = config.get('hooks', {})
                command.execute_hook(
                    hooks.get('before_everything'),
                    hooks.get('umask'),
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
        results = list(run_configuration(config_filename, config, arguments))
        error_logs = tuple(result for result in results if isinstance(result, logging.LogRecord))

        if error_logs:
            yield from log_error_records(
                '{}: Error running configuration file'.format(config_filename)
            )
            yield from error_logs
        else:
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.INFO,
                    levelname='INFO',
                    msg='{}: Successfully ran configuration file'.format(config_filename),
                )
            )
            if results:
                json_results.extend(results)

    if 'umount' in arguments:
        logger.info('Unmounting mount point {}'.format(arguments['umount'].mount_point))
        try:
            borg_umount.unmount_archive(
                mount_point=arguments['umount'].mount_point, local_path=get_local_path(configs),
            )
        except (CalledProcessError, OSError) as error:
            yield from log_error_records('Error unmounting mount point', error)

    if json_results:
        sys.stdout.write(json.dumps(json_results))

    if 'create' in arguments:
        try:
            for config_filename, config in configs.items():
                hooks = config.get('hooks', {})
                command.execute_hook(
                    hooks.get('after_everything'),
                    hooks.get('umask'),
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


def main():  # pragma: no cover
    configure_signals()

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
        logger.critical('Error parsing arguments: {}'.format(' '.join(sys.argv)))
        exit_with_help_link()

    global_arguments = arguments['global']
    if global_arguments.version:
        print(pkg_resources.require('borgmatic')[0].version)
        sys.exit(0)
    if global_arguments.bash_completion:
        print(borgmatic.commands.completion.bash_completion())
        sys.exit(0)

    config_filenames = tuple(collect.collect_config_filenames(global_arguments.config_paths))
    configs, parse_logs = load_configurations(
        config_filenames, global_arguments.overrides, global_arguments.resolve_env
    )

    any_json_flags = any(
        getattr(sub_arguments, 'json', False) for sub_arguments in arguments.values()
    )
    colorama.init(
        autoreset=True,
        strip=not should_do_markup(global_arguments.no_color or any_json_flags, configs),
    )
    try:
        configure_logging(
            verbosity_to_log_level(global_arguments.verbosity),
            verbosity_to_log_level(global_arguments.syslog_verbosity),
            verbosity_to_log_level(global_arguments.log_file_verbosity),
            verbosity_to_log_level(global_arguments.monitoring_verbosity),
            global_arguments.log_file,
        )
    except (FileNotFoundError, PermissionError) as error:
        configure_logging(logging.CRITICAL)
        logger.critical('Error configuring logging: {}'.format(error))
        exit_with_help_link()

    logger.debug('Ensuring legacy configuration is upgraded')
    convert.guard_configuration_upgraded(LEGACY_CONFIG_PATH, config_filenames)

    summary_logs = parse_logs + list(collect_configuration_run_summary_logs(configs, arguments))
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
