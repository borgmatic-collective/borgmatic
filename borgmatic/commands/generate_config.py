from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from borgmatic.config import convert, generate, validate


DEFAULT_DESTINATION_CONFIG_FILENAME = '/etc/borgmatic/config.yaml'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser(description='Generate a sample borgmatic YAML configuration file.')
    parser.add_argument(
        '-d', '--destination',
        dest='destination_filename',
        default=DEFAULT_DESTINATION_CONFIG_FILENAME,
        help='Destination YAML configuration filename. Default: {}'.format(DEFAULT_DESTINATION_CONFIG_FILENAME),
    )

    return parser.parse_args(arguments)


def main():  # pragma: no cover
    try:
        args = parse_arguments(*sys.argv[1:])

        generate.generate_sample_configuration(args.destination_filename, validate.schema_filename())

        print('Generated a sample configuration file at {}.'.format(args.destination_filename))
        print()
        print('Please edit the file to suit your needs. The values are just representative.')
        print('All fields are optional except where indicated.')
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
