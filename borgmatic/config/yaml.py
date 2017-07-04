import logging
import sys
import warnings

import pkg_resources
import pykwalify.core
import pykwalify.errors
import ruamel.yaml.error


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
    warnings.simplefilter('ignore', ruamel.yaml.error.UnsafeLoaderWarning)
    logging.getLogger('pykwalify').setLevel(logging.CRITICAL)

    try:
        validator = pykwalify.core.Core(source_file=config_filename, schema_files=[schema_filename])
    except pykwalify.errors.CoreError as error:
        if 'do not exists on disk' in str(error):
            raise FileNotFoundError("No such file or directory: '{}'".format(config_filename))
        if 'Unable to load any data' in str(error):
            # If the YAML file has a syntax error, pykwalify's exception is particularly unhelpful.
            # So reach back to the originating exception from ruamel.yaml for something more useful.
            raise Validation_error(config_filename, (error.__context__,))
        raise

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


# FOR TESTING
if __name__ == '__main__':
    try:
        configuration = parse_configuration('sample/config.yaml', schema_filename())
        print(configuration)
    except Validation_error as error:
        display_validation_error(error)
