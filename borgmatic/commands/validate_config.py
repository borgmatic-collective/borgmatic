import logging
import sys
from argparse import ArgumentParser

from borgmatic.config import collect, validate

logger = logging.getLogger(__name__)


def parse_arguments(*arguments):
    '''
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    '''
    config_paths = collect.get_default_config_paths()

    parser = ArgumentParser(description='Validate borgmatic configuration file(s).')
    parser.add_argument(
        '-c',
        '--config',
        nargs='+',
        dest='config_paths',
        default=config_paths,
        help='Configuration filenames or directories, defaults to: {}'.format(
            ' '.join(config_paths)
        ),
    )

    return parser.parse_args(arguments)


def main():  # pragma: no cover
    args = parse_arguments(*sys.argv[1:])

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    config_filenames = tuple(collect.collect_config_filenames(args.config_paths))
    if len(config_filenames) == 0:
        logger.critical('No files to validate found')
        sys.exit(1)

    found_issues = False
    for config_filename in config_filenames:
        try:
            validate.parse_configuration(config_filename, validate.schema_filename())
        except (ValueError, OSError, validate.Validation_error) as error:
            logging.critical('{}: Error parsing configuration file'.format(config_filename))
            logging.critical(error)
            found_issues = True

    if found_issues:
        sys.exit(1)
    else:
        logger.info(
            'All given configuration files are valid: {}'.format(', '.join(config_filenames))
        )
