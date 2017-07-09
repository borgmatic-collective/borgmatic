from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from ruamel import yaml

from borgmatic import borg
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


def main():
    try:
        args = parse_arguments(*sys.argv[1:])

        generate.generate_sample_configuration(args.destination_filename, validate.schema_filename())
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
