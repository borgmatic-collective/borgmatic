import fnmatch
import os

import jsonschema
import ruamel.yaml

import borgmatic.config.arguments
from borgmatic.config import constants, environment, load, normalize, override


def schema_filename():
    '''
    Path to the installed YAML configuration schema file, used to validate and parse the
    configuration.

    Raise FileNotFoundError when the schema path does not exist.
    '''
    schema_path = os.path.join(os.path.dirname(borgmatic.config.__file__), 'schema.yaml')

    with open(schema_path):
        return schema_path


def load_schema(schema_path):  # pragma: no cover
    '''
    Given a schema filename path, load the schema and return it as a dict.

    Raise Validation_error if the schema could not be parsed.
    '''
    try:
        return load.load_configuration(schema_path)
    except (ruamel.yaml.error.YAMLError, RecursionError) as error:
        raise Validation_error(schema_path, (str(error),))


def format_json_error_path_element(path_element):
    '''
    Given a path element into a JSON data structure, format it for display as a string.
    '''
    if isinstance(path_element, int):
        return str(f'[{path_element}]')

    return str(f'.{path_element}')


def format_json_error(error):
    '''
    Given an instance of jsonschema.exceptions.ValidationError, format it for display as a string.
    '''
    if not error.path:
        return f'At the top level: {error.message}'

    formatted_path = ''.join(format_json_error_path_element(element) for element in error.path)
    return f"At '{formatted_path.lstrip('.')}': {error.message}"


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
        return (
            f'An error occurred while parsing a configuration file at {self.config_filename}:\n'
            + '\n'.join(error for error in self.errors)
        )


def apply_logical_validation(config_filename, parsed_configuration):
    '''
    Given a parsed and schematically valid configuration as a data structure of nested dicts (see
    below), run through any additional logical validation checks. If there are any such validation
    problems, raise a Validation_error.
    '''
    repositories = parsed_configuration.get('repositories')
    check_repositories = parsed_configuration.get('check_repositories', [])
    for repository in check_repositories:
        if not any(
            repositories_match(repository, config_repository) for config_repository in repositories
        ):
            raise Validation_error(
                config_filename,
                (f'Unknown repository in "check_repositories": {repository}',),
            )


def parse_configuration(
    config_filename, schema_filename, arguments, overrides=None, resolve_env=True
):
    '''
    Given the path to a config filename in YAML format, the path to a schema filename in a YAML
    rendition of JSON Schema format, arguments as dict from action name to argparse.Namespace, a
    sequence of configuration file override strings in the form of "option.suboption=value", and
    whether to resolve environment variables, return the parsed configuration as a data structure of
    nested dicts and lists corresponding to the schema. Example return value.

    Example return value:

        {
            'source_directories': ['/home', '/etc'],
            'repository': 'hostname.borg',
            'keep_daily': 7,
            'checks': ['repository', 'archives'],
        }

    Also return a set of loaded configuration paths and a sequence of logging.LogRecord instances
    containing any warnings about the configuration.

    Raise FileNotFoundError if the file does not exist, PermissionError if the user does not
    have permissions to read the file, or Validation_error if the config does not match the schema.
    '''
    config_paths = set()

    try:
        config = load.load_configuration(config_filename, config_paths)
        schema = load.load_configuration(schema_filename)
    except (ruamel.yaml.error.YAMLError, RecursionError) as error:
        raise Validation_error(config_filename, (str(error),))

    borgmatic.config.arguments.apply_arguments_to_config(config, schema, arguments)
    override.apply_overrides(config, schema, overrides)
    constants.apply_constants(config, config.get('constants') if config else {})

    if resolve_env:
        environment.resolve_env_variables(config)

    logs = normalize.normalize(config_filename, config)

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

    return config, config_paths, logs


def normalize_repository_path(repository, base=None):
    '''
    Given a repository path, return the absolute path of it (for local repositories).
    Optionally, use a base path for resolving relative paths, e.g. to the configured working directory.
    '''
    # A colon in the repository could mean that it's either a file:// URL or a remote repository.
    # If it's a remote repository, we don't want to normalize it. If it's a file:// URL, we do.
    if ':' not in repository:
        return (
            os.path.abspath(os.path.join(base, repository)) if base else os.path.abspath(repository)
        )
    elif repository.startswith('file://'):
        local_path = repository.partition('file://')[-1]
        return (
            os.path.abspath(os.path.join(base, local_path)) if base else os.path.abspath(local_path)
        )
    else:
        return repository


def glob_match(first, second):
    '''
    Given two strings, return whether the first matches the second. Globs are
    supported.
    '''
    if first is None or second is None:
        return False

    return fnmatch.fnmatch(first, second) or fnmatch.fnmatch(second, first)


def repositories_match(first, second):
    '''
    Given two repository dicts with keys "path" (relative and/or absolute),
    and "label", two repository paths as strings, or a mix of the two formats,
    return whether they match. Globs are supported.
    '''
    if isinstance(first, str):
        first = {'path': first, 'label': first}
    if isinstance(second, str):
        second = {'path': second, 'label': second}

    return glob_match(first.get('label'), second.get('label')) or glob_match(
        normalize_repository_path(first.get('path')), normalize_repository_path(second.get('path'))
    )


def guard_configuration_contains_repository(repository, configurations):
    '''
    Given a repository path and a dict mapping from config filename to corresponding parsed config
    dict, ensure that the repository is declared at least once in all of the configurations. If no
    repository is given, skip this check.

    Raise ValueError if the repository is not found in any configurations.
    '''
    if not repository:
        return

    count = len(
        tuple(
            config_repository
            for config in configurations.values()
            for config_repository in config['repositories']
            if repositories_match(config_repository, repository)
        )
    )

    if count == 0:
        raise ValueError(f'Repository "{repository}" not found in configuration files')
