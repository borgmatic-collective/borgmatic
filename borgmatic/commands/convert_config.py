from __future__ import print_function
from argparse import ArgumentParser
import os
from subprocess import CalledProcessError
import sys

from ruamel import yaml

from borgmatic import borg
from borgmatic.config import convert, generate, legacy, validate


DEFAULT_SOURCE_CONFIG_FILENAME = '/etc/borgmatic/config'
DEFAULT_SOURCE_EXCLUDES_FILENAME = '/etc/borgmatic/excludes'
DEFAULT_DESTINATION_CONFIG_FILENAME = '/etc/borgmatic/config.yaml'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser(
        description='''
            Convert legacy INI-style borgmatic configuration and excludes files to a single YAML
            configuration file. Note that this replaces any comments from the source files.
        '''
    )
    parser.add_argument(
        '-s', '--source-config',
        dest='source_config_filename',
        default=DEFAULT_SOURCE_CONFIG_FILENAME,
        help='Source INI-style configuration filename. Default: {}'.format(DEFAULT_SOURCE_CONFIG_FILENAME),
    )
    parser.add_argument(
        '-e', '--source-excludes',
        dest='source_excludes_filename',
        default=DEFAULT_SOURCE_EXCLUDES_FILENAME if os.path.exists(DEFAULT_SOURCE_EXCLUDES_FILENAME) else None,
        help='Excludes filename',
    )
    parser.add_argument(
        '-d', '--destination-config',
        dest='destination_config_filename',
        default=DEFAULT_DESTINATION_CONFIG_FILENAME,
        help='Destination YAML configuration filename. Default: {}'.format(DEFAULT_DESTINATION_CONFIG_FILENAME),
    )

    return parser.parse_args(arguments)


def main():  # pragma: no cover
    try:
        args = parse_arguments(*sys.argv[1:])
        schema = yaml.round_trip_load(open(validate.schema_filename()).read())
        source_config = legacy.parse_configuration(args.source_config_filename, legacy.CONFIG_FORMAT)
        source_excludes = (
            open(args.source_excludes_filename).read().splitlines()
            if args.source_excludes_filename
            else []
        )

        destination_config = convert.convert_legacy_parsed_config(source_config, source_excludes, schema)

        generate.write_configuration(args.destination_config_filename, destination_config)

        # TODO: As a backstop, check that the written config can actually be read and parsed, and
        # that it matches the destination config data structure that was written.
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
