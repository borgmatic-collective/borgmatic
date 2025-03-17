import io
import logging

import ruamel.yaml

logger = logging.getLogger(__name__)


def set_values(config, keys, value):
    '''
    Given a hierarchy of configuration dicts, a sequence of parsed key strings, and a string value,
    descend into the hierarchy based on the keys to set the value into the right place.
    '''
    if not keys:
        return

    first_key = keys[0]
    if len(keys) == 1:
        if isinstance(config, list):
            raise ValueError(
                'When overriding a list option, the value must use list syntax (e.g., "[foo, bar]" or "[{key: value}]" as appropriate)'
            )

        config[first_key] = value
        return

    if first_key not in config:
        config[first_key] = {}

    set_values(config[first_key], keys[1:], value)


def convert_value_type(value, option_type):
    '''
    Given a string value and its schema type as a string, determine its logical type (string,
    boolean, integer, etc.), and return it converted to that type.

    If the option type is a string, leave the value as a string so that special characters in it
    don't get interpreted as YAML during conversion.

    Raise ruamel.yaml.error.YAMLError if there's a parse issue with the YAML.
    '''
    if option_type == 'string':
        return value

    return ruamel.yaml.YAML(typ='safe').load(io.StringIO(value))


LEGACY_SECTION_NAMES = {'location', 'storage', 'retention', 'consistency', 'output', 'hooks'}


def strip_section_names(parsed_override_key):
    '''
    Given a parsed override key as a tuple of option and suboption names, strip out any initial
    legacy section names, since configuration file normalization also strips them out.
    '''
    if parsed_override_key[0] in LEGACY_SECTION_NAMES:
        return parsed_override_key[1:]

    return parsed_override_key


def type_for_option(schema, option_keys):
    '''
    Given a configuration schema and a sequence of keys identifying an option, e.g.
    ('extra_borg_options', 'init'), return the schema type of that option as a string.

    Return None if the option or its type cannot be found in the schema.
    '''
    option_schema = schema

    for key in option_keys:
        try:
            option_schema = option_schema['properties'][key]
        except KeyError:
            return None

    try:
        return option_schema['type']
    except KeyError:
        return None


def parse_overrides(raw_overrides, schema):
    '''
    Given a sequence of configuration file override strings in the form of "option.suboption=value"
    and a configuration schema dict, parse and return a sequence of tuples (keys, values), where
    keys is a sequence of strings. For instance, given the following raw overrides:

        ['my_option.suboption=value1', 'other_option=value2']

    ... return this:

        (
            (('my_option', 'suboption'), 'value1'),
            (('other_option'), 'value2'),
        )

    Raise ValueError if an override can't be parsed.
    '''
    if not raw_overrides:
        return ()

    parsed_overrides = []

    for raw_override in raw_overrides:
        try:
            raw_keys, value = raw_override.split('=', 1)
            keys = tuple(raw_keys.split('.'))
            option_type = type_for_option(schema, keys)

            parsed_overrides.append(
                (
                    keys,
                    convert_value_type(value, option_type),
                )
            )
        except ValueError:
            raise ValueError(
                f"Invalid override '{raw_override}'. Make sure you use the form: OPTION=VALUE or OPTION.SUBOPTION=VALUE"
            )
        except ruamel.yaml.error.YAMLError as error:
            raise ValueError(f"Invalid override '{raw_override}': {error.problem}")

    return tuple(parsed_overrides)


def apply_overrides(config, schema, raw_overrides):
    '''
    Given a configuration dict, a corresponding configuration schema dict, and a sequence of
    configuration file override strings in the form of "option.suboption=value", parse each override
    and set it into the configuration dict.

    Set the overrides into the configuration both with and without deprecated section names (if
    used), so that the overrides work regardless of whether the configuration is also using
    deprecated section names.
    '''
    overrides = parse_overrides(raw_overrides, schema)

    if overrides:
        logger.warning(
            "The --override flag is deprecated and will be removed from a future release. Instead, use a command-line flag corresponding to the configuration option you'd like to set."
        )

    for keys, value in overrides:
        set_values(config, keys, value)
        set_values(config, strip_section_names(keys), value)
