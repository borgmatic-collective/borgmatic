import os

import jsonschema
import pkg_resources
import ruamel.yaml

from borgmatic.config import load, normalize, override


def schema_filename():
    '''
    Path to the installed YAML configuration schema file, used to validate and parse the
    configuration.
    '''
    return pkg_resources.resource_filename('borgmatic', 'config/schema.yaml')


def format_json_error_path_element(path_element):
    '''
    Given a path element into a JSON data structure, format it for display as a string.
    '''
    if isinstance(path_element, int):
        return str('[{}]'.format(path_element))

    return str('.{}'.format(path_element))


def format_json_error(error):
    '''
    Given an instance of jsonschema.exceptions.ValidationError, format it for display as a string.
    '''
    if not error.path:
        return 'At the top level: {}'.format(error.message)

    formatted_path = ''.join(format_json_error_path_element(element) for element in error.path)
    return "At '{}': {}".format(formatted_path.lstrip('.'), error.message)


class Validation_error(ValueError):
    '''
    A collection of error messages generated when attempting to validate a particular
    configuration file.
    '''

    def __init__(self, config_filename, errors):
        '''
        Given a configuration filename path and a sequence of string error messages, create a
        Validation_error.
        '''
        self.config_filename = config_filename
        self.errors = errors

    def __str__(self):
        '''
        Render a validation error as a user-facing string.
        '''
        return 'An error occurred while parsing a configuration file at {}:\n'.format(
            self.config_filename
        ) + '\n'.join(error for error in self.errors)


def apply_logical_validation(config_filename, parsed_configuration):
    '''
    Given a parsed and schematically valid configuration as a data structure of nested dicts (see
    below), run through any additional logical validation checks. If there are any such validation
    problems, raise a Validation_error.
    '''
    location_repositories = parsed_configuration.get('location', {}).get('repositories')
    check_repositories = parsed_configuration.get('consistency', {}).get('check_repositories', [])
    for repository in check_repositories:
        if repository not in location_repositories:
            raise Validation_error(
                config_filename,
                (
                    'Unknown repository in the consistency section\'s check_repositories: {}'.format(
                        repository
                    ),
                ),
            )


def parse_configuration(config_filename, schema_filename, overrides=None):
    '''
    Given the path to a config filename in YAML format, the path to a schema filename in a YAML
    rendition of JSON Schema format, a sequence of configuration file override strings in the form
    of "section.option=value", return the parsed configuration as a data structure of nested dicts
    and lists corresponding to the schema. Example return value:

       {'location': {'source_directories': ['/home', '/etc'], 'repository': 'hostname.borg'},
       'retention': {'keep_daily': 7}, 'consistency': {'checks': ['repository', 'archives']}}

    Raise FileNotFoundError if the file does not exist, PermissionError if the user does not
    have permissions to read the file, or Validation_error if the config does not match the schema.
    '''
    try:
        config = load.load_configuration(config_filename)
        schema = load.load_configuration(schema_filename)
    except (ruamel.yaml.error.YAMLError, RecursionError) as error:
        raise Validation_error(config_filename, (str(error),))

    override.apply_overrides(config, overrides)
    normalize.normalize(config)

    try:
        validator = jsonschema.Draft7Validator(schema)
    except AttributeError:  # pragma: no cover
        validator = jsonschema.Draft4Validator(schema)
    validation_errors = tuple(validator.iter_errors(config))

    if validation_errors:
        raise Validation_error(
            config_filename, tuple(format_json_error(error) for error in validation_errors)
        )

    apply_logical_validation(config_filename, config)

    return config


def normalize_repository_path(repository):
    '''
    Given a repository path, return the absolute path of it (for local repositories).
    '''
    # A colon in the repository indicates it's a remote repository. Bail.
    if ':' in repository:
        return repository

    return os.path.abspath(repository)


def repositories_match(first, second):
    '''
    Given two repository paths (relative and/or absolute), return whether they match.
    '''
    return normalize_repository_path(first) == normalize_repository_path(second)


def guard_configuration_contains_repository(repository, configurations):
    '''
    Given a repository path and a dict mapping from config filename to corresponding parsed config
    dict, ensure that the repository is declared exactly once in all of the configurations.

    If no repository is given, then error if there are multiple configured repositories.

    Raise ValueError if the repository is not found in a configuration, or is declared multiple
    times.
    '''
    if not repository:
        count = len(
            tuple(
                config_repository
                for config in configurations.values()
                for config_repository in config['location']['repositories']
            )
        )

        if count > 1:
            raise ValueError(
                'Can\'t determine which repository to use. Use --repository option to disambiguate'
            )

        return

    count = len(
        tuple(
            config_repository
            for config in configurations.values()
            for config_repository in config['location']['repositories']
            if repositories_match(repository, config_repository)
        )
    )

    if count == 0:
        raise ValueError('Repository {} not found in configuration files'.format(repository))
    if count > 1:
        raise ValueError('Repository {} found in multiple configuration files'.format(repository))
