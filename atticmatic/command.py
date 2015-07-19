from __future__ import print_function
from argparse import ArgumentParser
from importlib import import_module
import os
from subprocess import CalledProcessError
import sys

from atticmatic.config import parse_configuration


DEFAULT_CONFIG_FILENAME_PATTERN = '/etc/{}/config'
DEFAULT_EXCLUDES_FILENAME_PATTERN = '/etc/{}/excludes'


def parse_arguments(command_name, *arguments):
    '''
    Given the name of the command with which this script was invoked and command-line arguments,
    parse the arguments and return them as an ArgumentParser instance. Use the command name to
    determine the default configuration and excludes paths.
    '''
    parser = ArgumentParser()
    parser.add_argument(
        '-c', '--config',
        dest='config_filename',
        default=DEFAULT_CONFIG_FILENAME_PATTERN.format(command_name),
        help='Configuration filename',
    )
    parser.add_argument(
        '--excludes',
        dest='excludes_filename',
        default=DEFAULT_EXCLUDES_FILENAME_PATTERN.format(command_name),
        help='Excludes filename',
    )
    parser.add_argument(
        '-v', '--verbosity',
        type=int,
        help='Display verbose progress (1 for some, 2 for lots)',
    )

    return parser.parse_args(arguments)


def load_backend(command_name):
    '''
    Given the name of the command with which this script was invoked, return the corresponding
    backend module responsible for actually dealing with backups.
    '''
    backend_name = {
        'atticmatic': 'attic',
        'borgmatic': 'borg',
    }.get(command_name, 'attic')

    return import_module('atticmatic.backends.{}'.format(backend_name))


def main():
    try:
        command_name = os.path.basename(sys.argv[0])
        args = parse_arguments(command_name, *sys.argv[1:])
        config = parse_configuration(args.config_filename)
        repository = config.location['repository']
        backend = load_backend(command_name)

        backend.create_archive(args.excludes_filename, args.verbosity, **config.location)
        backend.prune_archives(args.verbosity, repository, config.retention)
        backend.check_archives(args.verbosity, repository, config.consistency)
    except (ValueError, IOError, CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
