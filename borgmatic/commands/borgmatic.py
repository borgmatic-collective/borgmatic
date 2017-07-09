from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from borgmatic import borg
from borgmatic.config.validate import parse_configuration, schema_filename


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
        default=DEFAULT_EXCLUDES_FILENAME if os.path.exists(DEFAULT_EXCLUDES_FILENAME) else None,
        help='Excludes filename',
    )
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        help='Display verbose progress (1 for some, 2 for lots)',
    )

    return parser.parse_args(arguments)


def main():
    try:
        # TODO: Detect whether only legacy config is present. If so, inform the user about how to
        # upgrade, then exet.

        args = parse_arguments(*sys.argv[1:])
        config = parse_configuration(args.config_filename, schema_filename())
        repository = config.location['repository']
        remote_path = config.location.get('remote_path')

        borg.initialize(config.storage)
        borg.create_archive(
            args.excludes_filename, args.verbosity, config.storage, **config.location
        )
        borg.prune_archives(args.verbosity, repository, config.retention, remote_path=remote_path)
        borg.check_archives(args.verbosity, repository, config.consistency, remote_path=remote_path)
    except (ValueError, OSError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
