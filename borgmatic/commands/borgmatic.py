from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from borgmatic import borg
from borgmatic.config import convert, validate


LEGACY_CONFIG_FILENAME = '/etc/borgmatic/config'
DEFAULT_CONFIG_FILENAME = '/etc/borgmatic/config.yaml'
DEFAULT_EXCLUDES_FILENAME = '/etc/borgmatic/excludes'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        dest='config_filename',
        default=DEFAULT_CONFIG_FILENAME,
        help='Configuration filename',
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
        convert.guard_configuration_upgraded(LEGACY_CONFIG_FILENAME, args.config_filename)
        config = validate.parse_configuration(args.config_filename, validate.schema_filename())
        repository = config['location']['repository']
        remote_path = config['location']['remote_path']
        (storage, retention, consistency) = (
            config.get(group_name, {})
            for group_name in ('storage', 'retention', 'consistency')
        )

        borg.initialize(storage)
        borg.prune_archives(args.verbosity, repository, retention, remote_path=remote_path)
        borg.create_archive(args.verbosity, storage, **config['location'])
        borg.check_archives(args.verbosity, repository, consistency, remote_path=remote_path)
    except (ValueError, OSError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
