import logging
import sys
import warnings

import pkg_resources
import pykwalify.core
import pykwalify.errors
from ruamel import yaml


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
    try:
        config = yaml.round_trip_load(open(config_filename))
        schema = yaml.round_trip_load(open(schema_filename))
    except yaml.error.YAMLError as error:
        raise Validation_error(config_filename, (str(error),))

    # pykwalify gets angry if the example field is not a string. So rather than bend to its will,
    # simply remove all examples before passing the schema to pykwalify.
    for section_name, section_schema in schema['map'].items():
        for field_name, field_schema in section_schema['map'].items():
            field_schema.pop('example', None)

    validator = pykwalify.core.Core(source_data=config, schema_data=schema)
    parsed_result = validator.validate(raise_exception=False)

    if validator.validation_errors:
        raise Validation_error(config_filename, validator.validation_errors)

    return parsed_result


def display_validation_error(validation_error):
    '''
    Given a Validation_error, display its error messages to stderr.
    '''
    print(
        'An error occurred while parsing a configuration file at {}:'.format(
            validation_error.config_filename
        ),
        file=sys.stderr,
    )

    for error in validation_error.error_messages:
        print(error, file=sys.stderr)
