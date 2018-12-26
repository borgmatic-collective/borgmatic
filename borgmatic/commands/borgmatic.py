from argparse import ArgumentParser
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
            If none of the --prune, --create, or --check options are given, then borgmatic defaults
            to all three: prune, create, and check archives.
            '''
    )
    parser.add_argument(
        '-c',
        '--config',
        nargs='+',
        dest='config_paths',
        default=config_paths,
        help='Configuration filenames or directories, defaults to: {}'.format(
            ' '.join(config_paths)
        ),
    )
    parser.add_argument(
        '--excludes',
        dest='excludes_filename',
        help='Deprecated in favor of exclude_patterns within configuration',
    )
    parser.add_argument(
        '-I', '--init', dest='init', action='store_true', help='Initialize an empty Borg repository'
    )
    parser.add_argument(
        '-e',
        '--encryption',
        dest='encryption_mode',
        help='Borg repository encryption mode (for use with --init)',
    )
    parser.add_argument(
        '--append-only',
        dest='append_only',
        action='store_true',
        help='Create an append-only repository (for use with --init)',
    )
    parser.add_argument(
        '--storage-quota',
        dest='storage_quota',
        help='Create a repository with a fixed storage quota (for use with --init)',
    )
    parser.add_argument(
        '-p',
        '--prune',
        dest='prune',
        action='store_true',
        help='Prune archives according to the retention policy',
    )
    parser.add_argument(
        '-C',
        '--create',
        dest='create',
        action='store_true',
        help='Create archives (actually perform backups)',
    )
    parser.add_argument(
        '-k', '--check', dest='check', action='store_true', help='Check archives for consistency'
    )
    parser.add_argument('-l', '--list', dest='list', action='store_true', help='List archives')
    parser.add_argument(
        '-i',
        '--info',
        dest='info',
        action='store_true',
        help='Display summary information on archives',
    )
    parser.add_argument(
        '--progress',
        dest='progress',
        default=False,
        action='store_true',
        help='Display progress with --create option for each file as it is backed up',
    )
    parser.add_argument(
        '--stats',
        dest='stats',
        default=False,
        action='store_true',
        help='Display statistics of archive with --create or --prune option',
    )
    parser.add_argument(
        '--json',
        dest='json',
        default=False,
        action='store_true',
        help='Output results from the --create, --list, or --info options as json',
    )
    parser.add_argument(
        '-n',
        '--dry-run',
        dest='dry_run',
        action='store_true',
        help='Go through the motions, but do not actually write to any repositories',
    )
    parser.add_argument(
        '-v',
        '--verbosity',
        type=int,
        choices=range(0, 3),
        default=0,
        help='Display verbose progress (1 for some, 2 for lots)',
    )
    parser.add_argument(
        '--version',
        dest='version',
        default=False,
        action='store_true',
        help='Display installed version number of borgmatic and exit',
    )

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

    if args.progress and not args.create:
        raise ValueError('The --progress option can only be used with the --create option')

    if args.stats and not (args.create or args.prune):
        raise ValueError('The --stats option can only be used with the --create or --prune options')

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
    if args.init or args.prune or args.create or args.check or args.list or args.info:
        return args

    args.prune = True
    args.create = True
    args.check = True
    return args


def run_configuration(config_filename, args):  # pragma: no cover
    '''
    Parse a single configuration file, and execute its defined pruning, backups, and/or consistency
    checks.
    '''
    logger.info('{}: Parsing configuration file'.format(config_filename))
    config = validate.parse_configuration(config_filename, validate.schema_filename())
    (location, storage, retention, consistency, hooks) = (
        config.get(section_name, {})
        for section_name in ('location', 'storage', 'retention', 'consistency', 'hooks')
    )

    try:
        local_path = location.get('local_path', 'borg')
        remote_path = location.get('remote_path')
        borg_environment.initialize(storage)

        if args.create:
            hook.execute_hook(hooks.get('before_backup'), config_filename, 'pre-backup')

        _run_commands(
            args=args,
            consistency=consistency,
            local_path=local_path,
            location=location,
            remote_path=remote_path,
            retention=retention,
            storage=storage,
        )

        if args.create:
            hook.execute_hook(hooks.get('after_backup'), config_filename, 'post-backup')
    except (OSError, CalledProcessError):
        hook.execute_hook(hooks.get('on_error'), config_filename, 'on-error')
        raise


def _run_commands(*, args, consistency, local_path, location, remote_path, retention, storage):
    json_results = []
    for unexpanded_repository in location['repositories']:
        _run_commands_on_repository(
            args=args,
            consistency=consistency,
            json_results=json_results,
            local_path=local_path,
            location=location,
            remote_path=remote_path,
            retention=retention,
            storage=storage,
            unexpanded_repository=unexpanded_repository,
        )
    if args.json:
        sys.stdout.write(json.dumps(json_results))


def _run_commands_on_repository(
    *,
    args,
    consistency,
    json_results,
    local_path,
    location,
    remote_path,
    retention,
    storage,
    unexpanded_repository
):  # pragma: no cover
    repository = os.path.expanduser(unexpanded_repository)
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
        borg_create.create_archive(
            args.dry_run,
            repository,
            location,
            storage,
            local_path=local_path,
            remote_path=remote_path,
            progress=args.progress,
            stats=args.stats,
        )
    if args.check and checks.repository_enabled_for_checks(repository, consistency):
        logger.info('{}: Running consistency checks'.format(repository))
        borg_check.check_archives(
            repository, storage, consistency, local_path=local_path, remote_path=remote_path
        )
    if args.list:
        logger.info('{}: Listing archives'.format(repository))
        output = borg_list.list_archives(
            repository, storage, local_path=local_path, remote_path=remote_path, json=args.json
        )
        if args.json:
            json_results.append(json.loads(output))
        else:
            sys.stdout.write(output)
    if args.info:
        logger.info('{}: Displaying summary info for archives'.format(repository))
        output = borg_info.display_archives_info(
            repository, storage, local_path=local_path, remote_path=remote_path, json=args.json
        )
        if args.json:
            json_results.append(json.loads(output))
        else:
            sys.stdout.write(output)


def collect_configuration_run_summary_logs(config_filenames, args):
    '''
    Given a sequence of configuration filenames and parsed command-line arguments as an
    argparse.ArgumentParser instance, run each configuration file and yield a series of
    logging.LogRecord instances containing summary information about each run.
    '''
    for config_filename in config_filenames:
        try:
            run_configuration(config_filename, args)
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

    if not config_filenames:
        yield logging.makeLogRecord(
            dict(
                levelno=logging.CRITICAL,
                msg='{}: No configuration files found'.format(' '.join(args.config_paths)),
            )
        )


def main():  # pragma: no cover
    configure_signals()
    args = parse_arguments(*sys.argv[1:])
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
        logger.critical('\nNeed some help? https://torsion.org/borgmatic/#issues')
        sys.exit(1)
