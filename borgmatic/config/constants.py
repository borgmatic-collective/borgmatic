import contextlib
import functools
import re
import shlex


def coerce_scalar(value):
    '''
    Given a configuration value, coerce it to an integer or a boolean as appropriate and return the
    result.
    '''
    with contextlib.suppress(TypeError, ValueError):
        return int(value)

    try:
        return {
            'true': True,
            'True': True,
            'false': False,
            'False': False,
        }.get(value, value)
    except TypeError:  # e.g. for an unhashable type
        return value


CONSTANT_PATTERN = re.compile(r'(?P<left_escape>\\)?\{(?P<name>[\w]+)(?P<right_escape>\\)?\}')


def resolve_constant(match, constants, command_hook):
    '''
    Given a re.Match instance of CONSTANT_PATTERN representing a matched constant name to be
    interpolated, a constants dict, and whether this is for a command hook, lookup the matched
    constant name within the given constants and return its value.

    If the match is escaped with backslashes, then instead of resolving the variable's value, strip
    off the backslashing and return the literal value.

    If the variable name isn't found in the given constants, then return the literal value.
    '''
    name = match.group('name')

    # The would-be variable is escaped, so strip off the escaping and return the result without
    # resolving the name—unless this is for a command hook, in which case just return the literal
    # string. That way, subsequent variable interpolation will still see the string as escaped
    # instead of trying to interpolate it.
    if match.group('left_escape') and match.group('right_escape'):
        if command_hook:
            return match.group(0)

        return '{' + name + '}'

    value = constants.get(name)

    # The matched variable is in the constants, so return its value. And if this is for a command
    # hook, then shell escape the value so as to prevent shell injection attacks.
    if value is not None:
        return shlex.quote(str(value)) if command_hook else str(value)

    # The matched variable name isn't in the constants. Return the whole string unaltered.
    return match.group(0)


def apply_constants(value, constants, command_hook=False):
    '''
    Given a configuration value (bool, dict, int, list, or string) and a dict of named constants,
    replace any configuration string values of the form "{constant}" (or containing it) with the
    value of the correspondingly named key from the constants. Recurse as necessary into nested
    configuration to find values to replace.

    For instance, if a configuration value contains "{foo}", replace it with the value of the "foo"
    key found within the configuration's "constants".

    If shell escape is True, then escape the constant's value before applying it.

    Return the configuration value and modify the original.
    '''
    if not value or not constants:
        return value

    if isinstance(value, str):
        # Support constants within non-string scalars by coercing the value to its appropriate type.
        value = coerce_scalar(
            CONSTANT_PATTERN.sub(
                functools.partial(resolve_constant, constants=constants, command_hook=command_hook),
                value,
            )
        )
    elif isinstance(value, list):
        for index, list_value in enumerate(value):
            value[index] = apply_constants(list_value, constants, command_hook)
    elif isinstance(value, dict):
        for option_name, option_value in value.items():
            value[option_name] = apply_constants(
                option_value,
                constants,
                command_hook=(
                    command_hook
                    or option_name.startswith(('before_', 'after_'))
                    or option_name in {'on_error', 'run'}
                ),
            )

    return value
