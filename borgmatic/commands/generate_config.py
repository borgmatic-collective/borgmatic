import sys
from argparse import ArgumentParser

from borgmatic.config import generate, validate

DEFAULT_DESTINATION_CONFIG_FILENAME = '/etc/borgmatic/config.yaml'


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    parser = ArgumentParser(description='Generate a sample borgmatic YAML configuration file.')
    parser.add_argument(
        '-s',
        '--source',
        dest='source_filename',
        help='Optional YAML configuration file to merge into the generated configuration, useful for upgrading your configuration',
    )
    parser.add_argument(
        '-d',
        '--destination',
        dest='destination_filename',
        default=DEFAULT_DESTINATION_CONFIG_FILENAME,
        help='Destination YAML configuration file. Default: {}'.format(
            DEFAULT_DESTINATION_CONFIG_FILENAME
        ),
    )

    return parser.parse_args(arguments)


def main():  # pragma: no cover
    try:
        args = parse_arguments(*sys.argv[1:])

        generate.generate_sample_configuration(
            args.source_filename, args.destination_filename, validate.schema_filename()
        )

        print('Generated a sample configuration file at {}.'.format(args.destination_filename))
        print()
        if args.source_filename:
            print(
                'Merged in the contents of configuration file at {}.'.format(args.source_filename)
            )
            print('To review the changes made, run:')
            print()
            print(
                '    diff --unified {} {}'.format(args.source_filename, args.destination_filename)
            )
            print()
        print('Please edit the file to suit your needs. The values are representative.')
        print('All fields are optional except where indicated.')
        print()
        print('If you ever need help: https://torsion.org/borgmatic/#issues')
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
