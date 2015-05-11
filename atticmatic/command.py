from __future__ import print_function
from argparse import ArgumentParser
from subprocess import CalledProcessError
import sys

from atticmatic.attic import check_archives, create_archive, prune_archives
from atticmatic.config import parse_configuration


DEFAULT_CONFIG_FILENAME = '/etc/atticmatic/config'
DEFAULT_EXCLUDES_FILENAME = '/etc/atticmatic/excludes'


def parse_arguments(*arguments):
    '''
    Parse the given command-line arguments and return them as an ArgumentParser instance.
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
        default=DEFAULT_EXCLUDES_FILENAME,
        help='Excludes filename',
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Display verbose progress information',
    )

    return parser.parse_args(arguments)


def main():
    try:
        args = parse_arguments(*sys.argv[1:])
        config = parse_configuration(args.config_filename)
        repository = config.location['repository']

        create_archive(args.excludes_filename, args.verbose, **config.location)
        prune_archives(args.verbose, repository, config.retention)
        check_archives(args.verbose, repository, config.consistency)
    except (ValueError, IOError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
