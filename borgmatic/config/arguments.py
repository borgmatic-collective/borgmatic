import io
import re

import ruamel.yaml


LIST_INDEX_KEY_PATTERN = re.compile(r'^(?P<list_name>[a-zA-z-]+)\[(?P<index>\d+)\]$')


def set_values(config, keys, value):
    '''
    Given a configuration dict, a sequence of parsed key strings, and a string value, descend into
    the configuration hierarchy based on the keys to set the value into the right place.
    '''
    if not keys:
        return

    first_key = keys[0]

    # Support "name[0]"-style list index syntax.
    match = LIST_INDEX_KEY_PATTERN.match(first_key)

    if match:
        list_key = match.group('list_name')
        list_index = int(match.group('index'))

        if len(keys) == 1:
            config[list_key][list_index] = value

            return

        if list_key not in config:
            config[list_key] = []

        try:
            set_values(config[list_key][list_index], keys[1:], value)
        except IndexError:
            raise ValueError(f'The list index {first_key} is out of range')

        return

    if len(keys) == 1:
        config[first_key] = value
        return

    if first_key not in config:
        config[first_key] = {}

    set_values(config[first_key], keys[1:], value)


def type_for_option(schema, option_keys):
    '''
    Given a configuration schema dict and a sequence of keys identifying a potentially nested
    option, e.g. ('extra_borg_options', 'create'), return the schema type of that option as a
    string.

    Return None if the option or its type cannot be found in the schema.
    '''
    option_schema = schema

    for key in option_keys:
        # Support "name[0]"-style list index syntax.
        match = LIST_INDEX_KEY_PATTERN.match(key)

        try:
            if match:
                option_schema = option_schema['properties'][match.group('list_name')]['items']
            else:
                option_schema = option_schema['properties'][key]
        except KeyError:
            return None

    try:
        return option_schema['type']
    except KeyError:
        return None


def prepare_arguments_for_config(global_arguments, schema):
    '''
    Given global arguments as an argparse.Namespace and a configuration schema dict, parse each
    argument that corresponds to an option in the schema and return a sequence of tuples (keys,
    values) for that option, where keys is a sequence of strings. For instance, given the following
    arguments:

        argparse.Namespace(**{'my_option.sub_option': 'value1', 'other_option': 'value2'})

    ... return this:

        (
            (('my_option', 'sub_option'), 'value1'),
            (('other_option'), 'value2'),
        )

    Raise ValueError if an override can't be parsed.
    '''
    prepared_values = []

    for argument_name, value in global_arguments.__dict__.items():
        try:
            if value is None:
                continue

            keys = tuple(argument_name.split('.'))
            option_type = type_for_option(schema, keys)

            # The argument doesn't correspond to any option in the schema, so ignore it. It's
            # probably a flag that borgmatic has on the command-line but not in configuration.
            if option_type is None:
                continue

            prepared_values.append(
                (
                    keys,
                    value,
                )
            )
        except ruamel.yaml.error.YAMLError as error:
            raise ValueError(f"Invalid override '{raw_override}': {error.problem}")

    return tuple(prepared_values)


def apply_arguments_to_config(config, schema, global_arguments):
    '''
    Given a configuration dict, a corresponding configuration schema dict, and global arguments as
    an argparse.Namespace, set those given argument values into their corresponding configuration
    options in the configuration dict.

    This supports argument flags of the from "--foo.bar.baz" where each dotted component is a nested
    configuration object. Additionally, flags like "--foo.bar[0].baz" are supported to update a list
    element in the configuration.
    '''

    for keys, value in prepare_arguments_for_config(global_arguments, schema):
        set_values(config, keys, value)
