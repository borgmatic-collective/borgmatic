from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from borgmatic import borg
from borgmatic.config import collect, convert, validate


LEGACY_CONFIG_PATH = '/etc/borgmatic/config'
DEFAULT_CONFIG_PATHS = ['/etc/borgmatic/config.yaml', '/etc/borgmatic.d']
DEFAULT_EXCLUDES_PATH = '/etc/borgmatic/excludes'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        nargs='+',
        dest='config_paths',
        default=DEFAULT_CONFIG_PATHS,
        help='Configuration filenames or directories, defaults to: {}'.format(' '.join(DEFAULT_CONFIG_PATHS)),
    )
    parser.add_argument(
        '--excludes',
        dest='excludes_filename',
        help='Excludes filename, deprecated in favor of exclude_patterns within configuration',
    )
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        help='Display verbose progress (1 for some, 2 for lots)',
    )

    return parser.parse_args(arguments)


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

            borg.initialize(storage)

            for repository in location['repositories']:
                borg.prune_archives(args.verbosity, repository, retention, remote_path=remote_path)
                borg.create_archive(
                    args.verbosity,
                    repository,
                    location,
                    storage,
                )
                borg.check_archives(args.verbosity, repository, consistency, remote_path=remote_path)
    except (ValueError, OSError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
