from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from borgmatic.borg import check, create, prune
from borgmatic.config import collect, convert, validate


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


def main():  # pragma: no cover
    try:
        args = parse_arguments(*sys.argv[1:])
        config_filenames = tuple(collect.collect_config_filenames(args.config_paths))
        convert.guard_configuration_upgraded(LEGACY_CONFIG_PATH, config_filenames)

        if len(config_filenames) == 0:
            raise ValueError('Error: No configuration files found in: {}'.format(' '.join(args.config_paths)))

        for config_filename in config_filenames:
            config = validate.parse_configuration(config_filename, validate.schema_filename())
            (location, storage, retention, consistency) = (
                config.get(section_name, {})
                for section_name in ('location', 'storage', 'retention', 'consistency')
            )
            remote_path = location.get('remote_path')

            create.initialize(storage)

            for repository in location['repositories']:
                if args.prune:
                    prune.prune_archives(args.verbosity, repository, retention, remote_path=remote_path)
                if args.create:
                    create.create_archive(
                        args.verbosity,
                        repository,
                        location,
                        storage,
                    )
                if args.check:
                    check.check_archives(args.verbosity, repository, consistency, remote_path=remote_path)
    except (ValueError, OSError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
