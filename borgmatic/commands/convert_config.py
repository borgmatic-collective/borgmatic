from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from ruamel import yaml

from borgmatic import borg
from borgmatic.config import convert, generate, legacy, validate


DEFAULT_SOURCE_CONFIG_FILENAME = '/etc/borgmatic/config'
# TODO: Fold excludes into the YAML config file.
DEFAULT_SOURCE_EXCLUDES_FILENAME = '/etc/borgmatic/excludes'
DEFAULT_DESTINATION_CONFIG_FILENAME = '/etc/borgmatic/config.yaml'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser(description='Convert a legacy INI-style borgmatic configuration file to YAML. Does not preserve comments.')
    parser.add_argument(
        '-s', '--source',
        dest='source_filename',
        default=DEFAULT_SOURCE_CONFIG_FILENAME,
        help='Source INI-style configuration filename. Default: {}'.format(DEFAULT_SOURCE_CONFIG_FILENAME),
    )
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
        source_config = legacy.parse_configuration(args.source_filename, legacy.CONFIG_FORMAT)
        schema = yaml.round_trip_load(open(validate.schema_filename()).read())

        destination_config = convert.convert_legacy_parsed_config(source_config, schema)

        generate.write_configuration(args.destination_filename, destination_config)

        # TODO: As a backstop, check that the written config can actually be read and parsed, and
        # that it matches the destination config data structure that was written.
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
