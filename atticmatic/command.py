from __future__ import print_function
from argparse import ArgumentParser
from subprocess import CalledProcessError
import sys

from atticmatic.attic import create_archive, prune_archives
from atticmatic.config import parse_configuration


def main():
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
    args = parser.parse_args()

    try:
        location_config, retention_config = parse_configuration(args.config_filename)

        create_archive(args.excludes_filename, args.verbose, *location_config)
        prune_archives(location_config.repository, args.verbose, *retention_config)
    except (ValueError, CalledProcessError), error:
        print(error, file=sys.stderr)
        sys.exit(1)
