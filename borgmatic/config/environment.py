import os
import re

VARIABLE_PATTERN = re.compile(
    r'(?P<escape>\\)?(?P<variable>\$\{(?P<name>[A-Za-z0-9_]+)((:?-)(?P<default>[^}]+))?\})'
)


def resolve_string(matcher):
    '''
    Given a matcher containing a name and an optional default value, get the value from environment.

    Raise ValueError if the variable is not defined in environment and no default value is provided.
    '''
    if matcher.group('escape') is not None:
        # In the case of an escaped environment variable, unescape it.
        return matcher.group('variable')

    # Resolve the environment variable.
    name, default = matcher.group('name'), matcher.group('default')
    out = os.getenv(name, default=default)

    if out is None:
        raise ValueError(f'Cannot find variable {name} in environment')

    return out


def resolve_env_variables(item):
    '''
    Resolves variables like or ${FOO} from given configuration with values from process environment.

    Supported formats:

     * ${FOO} will return FOO env variable
     * ${FOO-bar} or ${FOO:-bar} will return FOO env variable if it exists, else "bar"

    Raise if any variable is missing in environment and no default value is provided.
    '''
    if isinstance(item, str):
        return VARIABLE_PATTERN.sub(resolve_string, item)

    if isinstance(item, list):
        for index, subitem in enumerate(item):
            item[index] = resolve_env_variables(subitem)

    if isinstance(item, dict):
        for key, value in item.items():
            item[key] = resolve_env_variables(value)

    return item
