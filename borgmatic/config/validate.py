import logging

import pkg_resources
import pykwalify.core
import pykwalify.errors
import ruamel.yaml

from borgmatic.config import load


def schema_filename():
    '''
    Path to the installed YAML configuration schema file, used to validate and parse the
    configuration.
    '''
    return pkg_resources.resource_filename('borgmatic', 'config/schema.yaml')


class Validation_error(ValueError):
    '''
    A collection of error message strings generated when attempting to validate a particular
    configurartion file.
    '''

    def __init__(self, config_filename, error_messages):
        self.config_filename = config_filename
        self.error_messages = error_messages

    def __str__(self):
        '''
        Render a validation error as a user-facing string.
        '''
        return 'An error occurred while parsing a configuration file at {}:\n'.format(
            self.config_filename
        ) + '\n'.join(self.error_messages)


def apply_logical_validation(config_filename, parsed_configuration):
    '''
    Given a parsed and schematically valid configuration as a data structure of nested dicts (see
    below), run through any additional logical validation checks. If there are any such validation
    problems, raise a Validation_error.
    '''
    archive_name_format = parsed_configuration.get('storage', {}).get('archive_name_format')
    prefix = parsed_configuration.get('retention', {}).get('prefix')

    if archive_name_format and not prefix:
        raise Validation_error(
            config_filename,
            ('If you provide an archive_name_format, you must also specify a retention prefix.',),
        )

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


def remove_examples(schema):
    '''
    pykwalify gets angry if the example field is not a string. So rather than bend to its will,
    remove all examples from the given schema before passing the schema to pykwalify.
    '''
    if 'map' in schema:
        for item_name, item_schema in schema['map'].items():
            item_schema.pop('example', None)
            remove_examples(item_schema)
    elif 'seq' in schema:
        for item_schema in schema['seq']:
            item_schema.pop('example', None)
            remove_examples(item_schema)

    return schema


def parse_configuration(config_filename, schema_filename):
    '''
    Given the path to a config filename in YAML format and the path to a schema filename in
    pykwalify YAML schema format, return the parsed configuration as a data structure of nested
    dicts and lists corresponding to the schema. Example return value:

       {'location': {'source_directories': ['/home', '/etc'], 'repository': 'hostname.borg'},
       'retention': {'keep_daily': 7}, 'consistency': {'checks': ['repository', 'archives']}}

    Raise FileNotFoundError if the file does not exist, PermissionError if the user does not
    have permissions to read the file, or Validation_error if the config does not match the schema.
    '''
    logging.getLogger('pykwalify').setLevel(logging.ERROR)

    try:
        config = load.load_configuration(config_filename)
        schema = load.load_configuration(schema_filename)
    except (ruamel.yaml.error.YAMLError, RecursionError) as error:
        raise Validation_error(config_filename, (str(error),))

    validator = pykwalify.core.Core(source_data=config, schema_data=remove_examples(schema))
    parsed_result = validator.validate(raise_exception=False)

    if validator.validation_errors:
        raise Validation_error(config_filename, validator.validation_errors)

    apply_logical_validation(config_filename, parsed_result)

    return parsed_result


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
                'Can\'t determine which repository to use. Use --repository option to disambiguate'.format(
                    repository
                )
            )

        return

    count = len(
        tuple(
            config_repository
            for config in configurations.values()
            for config_repository in config['location']['repositories']
            if repository == config_repository
        )
    )

    if count == 0:
        raise ValueError('Repository {} not found in configuration files'.format(repository))
    if count > 1:
        raise ValueError('Repository {} found in multiple configuration files'.format(repository))
