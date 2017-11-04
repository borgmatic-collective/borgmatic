
from argparse import ArgumentParser
import logging
import os
from subprocess import CalledProcessError
import sys

from borgmatic.borg import check, create, prune
from borgmatic.commands import hook
from borgmatic.config import collect, convert, validate
from borgmatic.signals import configure_signals
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS, verbosity_to_log_level


logger = logging.getLogger(__name__)


LEGACY_CONFIG_PATH = '/etc/borgmatic/config'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser(
        description=
            '''
            A simple wrapper script for the Borg backup software that creates and prunes backups.
            If none of the --prune, --create, or --check options are given, then borgmatic defaults
            to all three: prune, create, and check archives.
            '''
    )
    parser.add_argument(
        '-c', '--config',
        nargs='+',
        dest='config_paths',
        default=collect.DEFAULT_CONFIG_PATHS,
        help='Configuration filenames or directories, defaults to: {}'.format(' '.join(collect.DEFAULT_CONFIG_PATHS)),
    )
    parser.add_argument(
        '--excludes',
        dest='excludes_filename',
        help='Deprecated in favor of exclude_patterns within configuration',
    )
    parser.add_argument(
        '-p', '--prune',
        dest='prune',
        action='store_true',
        help='Prune archives according to the retention policy',
    )
    parser.add_argument(
        '-C', '--create',
        dest='create',
        action='store_true',
        help='Create archives (actually perform backups)',
    )
    parser.add_argument(
        '-k', '--check',
        dest='check',
        action='store_true',
        help='Check archives for consistency',
    )
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        help='Display verbose progress (1 for some, 2 for lots)',
    )

    args = parser.parse_args(arguments)

    # If any of the three action flags in the given parse arguments have been explicitly requested,
    # leave them as-is. Otherwise, assume defaults: Mutate the given arguments to enable all the
    # actions.
    if not args.prune and not args.create and not args.check:
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
        remote_path = location.get('remote_path')
        create.initialize_environment(storage)
        hook.execute_hook(hooks.get('before_backup'), config_filename, 'pre-backup')

        for unexpanded_repository in location['repositories']:
            repository = os.path.expanduser(unexpanded_repository)
            if args.prune:
                logger.info('{}: Pruning archives'.format(repository))
                prune.prune_archives(args.verbosity, repository, retention, remote_path=remote_path)
            if args.create:
                logger.info('{}: Creating archive'.format(repository))
                create.create_archive(
                    args.verbosity,
                    repository,
                    location,
                    storage,
                )
            if args.check:
                logger.info('{}: Running consistency checks'.format(repository))
                check.check_archives(args.verbosity, repository, consistency, remote_path=remote_path)

        hook.execute_hook(hooks.get('after_backup'), config_filename, 'post-backup')
    except (OSError, CalledProcessError):
        hook.execute_hook(hooks.get('on_error'), config_filename, 'on-error')
        raise


def main():  # pragma: no cover
    try:
        configure_signals()
        args = parse_arguments(*sys.argv[1:])
        logging.basicConfig(level=verbosity_to_log_level(args.verbosity), format='%(message)s')

        config_filenames = tuple(collect.collect_config_filenames(args.config_paths))
        logger.debug('Ensuring legacy configuration is upgraded')
        convert.guard_configuration_upgraded(LEGACY_CONFIG_PATH, config_filenames)

        if len(config_filenames) == 0:
            raise ValueError('Error: No configuration files found in: {}'.format(' '.join(args.config_paths)))

        for config_filename in config_filenames:
            run_configuration(config_filename, args)
    except (ValueError, OSError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
