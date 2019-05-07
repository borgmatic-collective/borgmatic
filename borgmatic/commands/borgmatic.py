from argparse import ArgumentParser
import collections
import json
import logging
import os
from subprocess import CalledProcessError
import sys

import pkg_resources

from borgmatic.borg import (
    check as borg_check,
    create as borg_create,
    environment as borg_environment,
    prune as borg_prune,
    extract as borg_extract,
    list as borg_list,
    info as borg_info,
    init as borg_init,
)
from borgmatic.commands import hook
from borgmatic.config import checks, collect, convert, validate
from borgmatic.signals import configure_signals
from borgmatic.verbosity import verbosity_to_log_level


logger = logging.getLogger(__name__)


LEGACY_CONFIG_PATH = '/etc/borgmatic/config'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an argparse.ArgumentParser instance.
    '''
    config_paths = collect.get_default_config_paths()

    parser = ArgumentParser(
        description='''
            A simple wrapper script for the Borg backup software that creates and prunes backups.
            If none of the action options are given, then borgmatic defaults to: prune, create, and
            check archives.
            ''',
        add_help=False,
    )

    actions_group = parser.add_argument_group('actions')
    actions_group.add_argument(
        '-I', '--init', dest='init', action='store_true', help='Initialize an empty Borg repository'
    )
    actions_group.add_argument(
        '-p',
        '--prune',
        dest='prune',
        action='store_true',
        help='Prune archives according to the retention policy',
    )
    actions_group.add_argument(
        '-C',
        '--create',
        dest='create',
        action='store_true',
        help='Create archives (actually perform backups)',
    )
    actions_group.add_argument(
        '-k', '--check', dest='check', action='store_true', help='Check archives for consistency'
    )

    actions_group.add_argument(
        '-x',
        '--extract',
        dest='extract',
        action='store_true',
        help='Extract a named archive to the current directory',
    )
    actions_group.add_argument(
        '-l', '--list', dest='list', action='store_true', help='List archives'
    )
    actions_group.add_argument(
        '-i',
        '--info',
        dest='info',
        action='store_true',
        help='Display summary information on archives',
    )

    init_group = parser.add_argument_group('options for --init')
    init_group.add_argument(
        '-e', '--encryption', dest='encryption_mode', help='Borg repository encryption mode'
    )
    init_group.add_argument(
        '--append-only',
        dest='append_only',
        action='store_true',
        help='Create an append-only repository',
    )
    init_group.add_argument(
        '--storage-quota',
        dest='storage_quota',
        help='Create a repository with a fixed storage quota',
    )

    prune_group = parser.add_argument_group('options for --prune')
    stats_argument = prune_group.add_argument(
        '--stats',
        dest='stats',
        default=False,
        action='store_true',
        help='Display statistics of archive',
    )

    create_group = parser.add_argument_group('options for --create')
    progress_argument = create_group.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress for each file as it is processed',
    )
    create_group._group_actions.append(stats_argument)
    json_argument = create_group.add_argument(
        '--json', dest='json', default=False, action='store_true', help='Output results as JSON'
    )

    extract_group = parser.add_argument_group('options for --extract')
    repository_argument = extract_group.add_argument(
        '--repository',
        help='Path of repository to use, defaults to the configured repository if there is only one',
    )
    archive_argument = extract_group.add_argument('--archive', help='Name of archive to operate on')
    extract_group.add_argument(
        '--restore-path',
        nargs='+',
        dest='restore_paths',
        help='Paths to restore from archive, defaults to the entire archive',
    )
    extract_group._group_actions.append(progress_argument)

    list_group = parser.add_argument_group('options for --list')
    list_group._group_actions.append(repository_argument)
    list_group._group_actions.append(archive_argument)
    list_group._group_actions.append(json_argument)

    info_group = parser.add_argument_group('options for --info')
    info_group._group_actions.append(json_argument)

    common_group = parser.add_argument_group('common options')
    common_group.add_argument(
        '-c',
        '--config',
        nargs='+',
        dest='config_paths',
        default=config_paths,
        help='Configuration filenames or directories, defaults to: {}'.format(
            ' '.join(config_paths)
        ),
    )
    common_group.add_argument(
        '--excludes',
        dest='excludes_filename',
        help='Deprecated in favor of exclude_patterns within configuration',
    )
    common_group.add_argument(
        '-n',
        '--dry-run',
        dest='dry_run',
        action='store_true',
        help='Go through the motions, but do not actually write to any repositories',
    )
    common_group.add_argument(
        '-v',
        '--verbosity',
        type=int,
        choices=range(0, 3),
        default=0,
        help='Display verbose progress (1 for some, 2 for lots)',
    )
    common_group.add_argument(
        '--version',
        dest='version',
        default=False,
        action='store_true',
        help='Display installed version number of borgmatic and exit',
    )
    common_group.add_argument('--help', action='help', help='Show this help information and exit')

    args = parser.parse_args(arguments)

    if args.excludes_filename:
        raise ValueError(
            'The --excludes option has been replaced with exclude_patterns in configuration'
        )

    if (args.encryption_mode or args.append_only or args.storage_quota) and not args.init:
        raise ValueError(
            'The --encryption, --append-only, and --storage-quota options can only be used with the --init option'
        )

    if args.init and args.dry_run:
        raise ValueError('The --init option cannot be used with the --dry-run option')
    if args.init and not args.encryption_mode:
        raise ValueError('The --encryption option is required with the --init option')

    if not args.extract:
        if not args.list:
            if args.repository:
                raise ValueError(
                    'The --repository option can only be used with the --extract and --list options'
                )
            if args.archive:
                raise ValueError(
                    'The --archive option can only be used with the --extract and --list options'
                )
        if args.restore_paths:
            raise ValueError('The --restore-path option can only be used with the --extract option')
    if args.extract and not args.archive:
        raise ValueError('The --archive option is required with the --extract option')

    if args.progress and not (args.create or args.extract):
        raise ValueError(
            'The --progress option can only be used with the --create and --extract options'
        )

    if args.json and not (args.create or args.list or args.info):
        raise ValueError(
            'The --json option can only be used with the --create, --list, or --info options'
        )

    if args.json and args.list and args.info:
        raise ValueError(
            'With the --json option, options --list and --info cannot be used together'
        )

    # If any of the action flags are explicitly requested, leave them as-is. Otherwise, assume
    # defaults: Mutate the given arguments to enable the default actions.
    if (
        not args.init
        and not args.prune
        and not args.create
        and not args.check
        and not args.extract
        and not args.list
        and not args.info
    ):
        args.prune = True
        args.create = True
        args.check = True

    if args.stats and not (args.create or args.prune):
        raise ValueError('The --stats option can only be used when creating or pruning archives')

    return args


def run_configuration(config_filename, config, args):  # pragma: no cover
    '''
    Given a config filename and the corresponding parsed config dict, execute its defined pruning,
    backups, consistency checks, and/or other actions.

    Yield JSON output strings from executing any actions that produce JSON.
    '''
    (location, storage, retention, consistency, hooks) = (
        config.get(section_name, {})
        for section_name in ('location', 'storage', 'retention', 'consistency', 'hooks')
    )

    try:
        local_path = location.get('local_path', 'borg')
        remote_path = location.get('remote_path')
        borg_environment.initialize(storage)

        if args.create:
            hook.execute_hook(
                hooks.get('before_backup'), config_filename, 'pre-backup', args.dry_run
            )

        for repository_path in location['repositories']:
            yield from run_actions(
                args=args,
                location=location,
                storage=storage,
                retention=retention,
                consistency=consistency,
                local_path=local_path,
                remote_path=remote_path,
                repository_path=repository_path,
            )

        if args.create:
            hook.execute_hook(
                hooks.get('after_backup'), config_filename, 'post-backup', args.dry_run
            )
    except (OSError, CalledProcessError):
        hook.execute_hook(hooks.get('on_error'), config_filename, 'on-error', args.dry_run)
        raise


def run_actions(
    *, args, location, storage, retention, consistency, local_path, remote_path, repository_path
):  # pragma: no cover
    '''
    Given parsed command-line arguments as an argparse.ArgumentParser instance, several different
    configuration dicts, local and remote paths to Borg, and a repository name, run all actions
    from the command-line arguments on the given repository.

    Yield JSON output strings from executing any actions that produce JSON.
    '''
    repository = os.path.expanduser(repository_path)
    dry_run_label = ' (dry run; not making any changes)' if args.dry_run else ''
    if args.init:
        logger.info('{}: Initializing repository'.format(repository))
        borg_init.initialize_repository(
            repository,
            args.encryption_mode,
            args.append_only,
            args.storage_quota,
            local_path=local_path,
            remote_path=remote_path,
        )
    if args.prune:
        logger.info('{}: Pruning archives{}'.format(repository, dry_run_label))
        borg_prune.prune_archives(
            args.dry_run,
            repository,
            storage,
            retention,
            local_path=local_path,
            remote_path=remote_path,
            stats=args.stats,
        )
    if args.create:
        logger.info('{}: Creating archive{}'.format(repository, dry_run_label))
        json_output = borg_create.create_archive(
            args.dry_run,
            repository,
            location,
            storage,
            local_path=local_path,
            remote_path=remote_path,
            progress=args.progress,
            stats=args.stats,
            json=args.json,
        )
        if json_output:
            yield json.loads(json_output)
    if args.check and checks.repository_enabled_for_checks(repository, consistency):
        logger.info('{}: Running consistency checks'.format(repository))
        borg_check.check_archives(
            repository, storage, consistency, local_path=local_path, remote_path=remote_path
        )
    if args.extract:
        if args.repository is None or repository == args.repository:
            logger.info('{}: Extracting archive {}'.format(repository, args.archive))
            borg_extract.extract_archive(
                args.dry_run,
                repository,
                args.archive,
                args.restore_paths,
                location,
                storage,
                local_path=local_path,
                remote_path=remote_path,
                progress=args.progress,
            )
    if args.list:
        if args.repository is None or repository == args.repository:
            logger.info('{}: Listing archives'.format(repository))
            json_output = borg_list.list_archives(
                repository,
                storage,
                args.archive,
                local_path=local_path,
                remote_path=remote_path,
                json=args.json,
            )
            if json_output:
                yield json.loads(json_output)
    if args.info:
        logger.info('{}: Displaying summary info for archives'.format(repository))
        json_output = borg_info.display_archives_info(
            repository, storage, local_path=local_path, remote_path=remote_path, json=args.json
        )
        if json_output:
            yield json.loads(json_output)


def collect_configuration_run_summary_logs(config_filenames, args):
    '''
    Given a sequence of configuration filenames and parsed command-line arguments as an
    argparse.ArgumentParser instance, run each configuration file and yield a series of
    logging.LogRecord instances containing summary information about each run.

    As a side effect of running through these configuration files, output their JSON results, if
    any, to stdout.
    '''
    # Dict mapping from config filename to corresponding parsed config dict.
    configs = collections.OrderedDict()

    # Parse and load each configuration file.
    for config_filename in config_filenames:
        try:
            logger.info('{}: Parsing configuration file'.format(config_filename))
            configs[config_filename] = validate.parse_configuration(
                config_filename, validate.schema_filename()
            )
        except (ValueError, OSError, validate.Validation_error) as error:
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.CRITICAL,
                    msg='{}: Error parsing configuration file'.format(config_filename),
                )
            )
            yield logging.makeLogRecord(dict(levelno=logging.CRITICAL, msg=error))

    # Run cross-file validation checks.
    if args.extract or (args.list and args.archive):
        try:
            validate.guard_configuration_contains_repository(args.repository, configs)
        except ValueError as error:
            yield logging.makeLogRecord(dict(levelno=logging.CRITICAL, msg=error))
            return

    # Execute the actions corresponding to each configuration file.
    json_results = []
    for config_filename, config in configs.items():
        try:
            json_results.extend(list(run_configuration(config_filename, config, args)))
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.INFO,
                    msg='{}: Successfully ran configuration file'.format(config_filename),
                )
            )
        except (ValueError, OSError, CalledProcessError) as error:
            yield logging.makeLogRecord(
                dict(
                    levelno=logging.CRITICAL,
                    msg='{}: Error running configuration file'.format(config_filename),
                )
            )
            yield logging.makeLogRecord(dict(levelno=logging.CRITICAL, msg=error))

    if json_results:
        sys.stdout.write(json.dumps(json_results))

    if not config_filenames:
        yield logging.makeLogRecord(
            dict(
                levelno=logging.CRITICAL,
                msg='{}: No configuration files found'.format(' '.join(args.config_paths)),
            )
        )


def exit_with_help_link():  # pragma: no cover
    '''
    Display a link to get help and exit with an error code.
    '''
    logger.critical('\nNeed some help? https://torsion.org/borgmatic/#issues')
    sys.exit(1)


def main():  # pragma: no cover
    configure_signals()

    try:
        args = parse_arguments(*sys.argv[1:])
    except ValueError as error:
        logging.basicConfig(level=logging.CRITICAL, format='%(message)s')
        logger.critical(error)
        exit_with_help_link()

    logging.basicConfig(level=verbosity_to_log_level(args.verbosity), format='%(message)s')

    if args.version:
        print(pkg_resources.require('borgmatic')[0].version)
        sys.exit(0)

    config_filenames = tuple(collect.collect_config_filenames(args.config_paths))
    logger.debug('Ensuring legacy configuration is upgraded')
    convert.guard_configuration_upgraded(LEGACY_CONFIG_PATH, config_filenames)

    summary_logs = tuple(collect_configuration_run_summary_logs(config_filenames, args))

    logger.info('\nsummary:')
    [logger.handle(log) for log in summary_logs if log.levelno >= logger.getEffectiveLevel()]

    if any(log.levelno == logging.CRITICAL for log in summary_logs):
        exit_with_help_link()
