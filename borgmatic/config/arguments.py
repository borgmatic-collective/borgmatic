import io
import re

import ruamel.yaml

import borgmatic.config.schema

LIST_INDEX_KEY_PATTERN = re.compile(r'^(?P<list_name>[a-zA-z-]+)\[(?P<index>\d+)\]$')


def set_values(config, keys, value):
    '''
    Given a configuration dict, a sequence of parsed key strings, and a string value, descend into
    the configuration hierarchy based on the given keys and set the value into the right place.
    For example, consider these keys:

        ('foo', 'bar', 'baz')

    This looks up "foo" in the given configuration dict. And within that, it looks up "bar". And
    then within that, it looks up "baz" and sets it to the given value. Another example:

        ('mylist[0]', 'foo')

    This looks for the zeroth element of "mylist" in the given configuration. And within that, it
    looks up "foo" and sets it to the given value.
    '''
    if not keys:
        return

    first_key = keys[0]

    # Support "mylist[0]" list index syntax.
    match = LIST_INDEX_KEY_PATTERN.match(first_key)

    if match:
        list_key = match.group('list_name')
        list_index = int(match.group('index'))

        try:
            if len(keys) == 1:
                config[list_key][list_index] = value

                return

            if list_key not in config:
                config[list_key] = []

            set_values(config[list_key][list_index], keys[1:], value)
        except (IndexError, KeyError):
            raise ValueError(f'Argument list index {first_key} is out of range')

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
        properties = borgmatic.config.schema.get_properties(option_schema)

        try:
            if match:
                option_schema = properties[match.group('list_name')]['items']
            else:
                option_schema = properties[key]
        except KeyError:
            return None

    try:
        return option_schema['type']
    except KeyError:
        return None


def convert_value_type(value, option_type):
    '''
    Given a string value and its schema type as a string, determine its logical type (string,
    boolean, integer, etc.), and return it converted to that type.

    If the destination option type is a string, then leave the value as-is so that special
    characters in it don't get interpreted as YAML during conversion.

    And if the source value isn't a string, return it as-is.

    Raise ruamel.yaml.error.YAMLError if there's a parse issue with the YAML.
    Raise ValueError if the parsed value doesn't match the option type.
    '''
    if not isinstance(value, str):
        return value

    if option_type == 'string':
        return value

    try:
        parsed_value = ruamel.yaml.YAML(typ='safe').load(io.StringIO(value))
    except ruamel.yaml.error.YAMLError as error:
        raise ValueError(f'Argument value "{value}" is invalid: {error.problem}')

    if not isinstance(parsed_value, borgmatic.config.schema.parse_type(option_type)):
        raise ValueError(f'Argument value "{value}" is not of the expected type: {option_type}')

    return parsed_value


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
            (('other_option',), 'value2'),
        )
    '''
    prepared_values = []

    for argument_name, value in global_arguments.__dict__.items():
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
                convert_value_type(value, option_type),
            )
        )

    return tuple(prepared_values)


def apply_arguments_to_config(config, schema, arguments):
    '''
    Given a configuration dict, a corresponding configuration schema dict, and arguments as a dict
    from action name to argparse.Namespace, set those given argument values into their corresponding
    configuration options in the configuration dict.

    This supports argument flags of the from "--foo.bar.baz" where each dotted component is a nested
    configuration object. Additionally, flags like "--foo.bar[0].baz" are supported to update a list
    element in the configuration.
    '''
    for action_arguments in arguments.values():
        for keys, value in prepare_arguments_for_config(action_arguments, schema):
            set_values(config, keys, value)
