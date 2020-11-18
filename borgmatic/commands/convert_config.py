import os
import sys
import textwrap
from argparse import ArgumentParser

from ruamel import yaml

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
        '-s',
        '--source-config',
        dest='source_config_filename',
        default=DEFAULT_SOURCE_CONFIG_FILENAME,
        help='Source INI-style configuration filename. Default: {}'.format(
            DEFAULT_SOURCE_CONFIG_FILENAME
        ),
    )
    parser.add_argument(
        '-e',
        '--source-excludes',
        dest='source_excludes_filename',
        default=DEFAULT_SOURCE_EXCLUDES_FILENAME
        if os.path.exists(DEFAULT_SOURCE_EXCLUDES_FILENAME)
        else None,
        help='Excludes filename',
    )
    parser.add_argument(
        '-d',
        '--destination-config',
        dest='destination_config_filename',
        default=DEFAULT_DESTINATION_CONFIG_FILENAME,
        help='Destination YAML configuration filename. Default: {}'.format(
            DEFAULT_DESTINATION_CONFIG_FILENAME
        ),
    )

    return parser.parse_args(arguments)


TEXT_WRAP_CHARACTERS = 80


def display_result(args):  # pragma: no cover
    result_lines = textwrap.wrap(
        'Your borgmatic configuration has been upgraded. Please review the result in {}.'.format(
            args.destination_config_filename
        ),
        TEXT_WRAP_CHARACTERS,
    )

    delete_lines = textwrap.wrap(
        'Once you are satisfied, you can safely delete {}{}.'.format(
            args.source_config_filename,
            ' and {}'.format(args.source_excludes_filename)
            if args.source_excludes_filename
            else '',
        ),
        TEXT_WRAP_CHARACTERS,
    )

    print('\n'.join(result_lines))
    print()
    print('\n'.join(delete_lines))


def main():  # pragma: no cover
    try:
        args = parse_arguments(*sys.argv[1:])
        schema = yaml.round_trip_load(open(validate.schema_filename()).read())
        source_config = legacy.parse_configuration(
            args.source_config_filename, legacy.CONFIG_FORMAT
        )
        source_config_file_mode = os.stat(args.source_config_filename).st_mode
        source_excludes = (
            open(args.source_excludes_filename).read().splitlines()
            if args.source_excludes_filename
            else []
        )

        destination_config = convert.convert_legacy_parsed_config(
            source_config, source_excludes, schema
        )

        generate.write_configuration(
            args.destination_config_filename,
            generate.render_configuration(destination_config),
            mode=source_config_file_mode,
        )

        display_result(args)
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
