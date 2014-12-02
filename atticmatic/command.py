from __future__ import print_function
from argparse import ArgumentParser
from subprocess import CalledProcessError
import sys

from atticmatic.attic import create_archive, prune_archives
from atticmatic.config import parse_configuration


def parse_arguments():
    '''
    Parse the command-line arguments from sys.argv and return them as an ArgumentParser instance.
    '''
    parser = ArgumentParser()
    parser.add_argument(
        '--config',
        dest='config_filename',
        default='/etc/atticmatic/config',
        help='Configuration filename',
    )
    parser.add_argument(
        '--excludes',
        dest='excludes_filename',
        default='/etc/atticmatic/excludes',
        help='Excludes filename',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Display verbose progress information',
    )

    return parser.parse_args()


def main():
    try:
        args = parse_arguments()
        location_config, retention_config = parse_configuration(args.config_filename)

        create_archive(args.excludes_filename, args.verbose, *location_config)
        prune_archives(location_config.repository, args.verbose, *retention_config)
    except (ValueError, IOError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
