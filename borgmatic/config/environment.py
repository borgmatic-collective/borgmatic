import os
import re

_VARIABLE_PATTERN = re.compile(
    r'(?P<escape>\\)?(?P<variable>\$\{(?P<name>[A-Za-z0-9_]+)((:?-)(?P<default>[^}]+))?\})'
)


def _resolve_string(matcher):
    '''
    Get the value from environment given a matcher containing a name and an optional default value.
    If the variable is not defined in environment and no default value is provided, an Error is raised.
    '''
    if matcher.group('escape') is not None:
        # in case of escaped envvar, unescape it
        return matcher.group('variable')
    # resolve the env var
    name, default = matcher.group('name'), matcher.group('default')
    out = os.getenv(name, default=default)
    if out is None:
        raise ValueError('Cannot find variable ${name} in environment'.format(name=name))
    return out


def resolve_env_variables(item):
    '''
    Resolves variables like or ${FOO} from given configuration with values from process environment
    Supported formats:
     - ${FOO} will return FOO env variable
     - ${FOO-bar} or ${FOO:-bar} will return FOO env variable if it exists, else "bar"

    If any variable is missing in environment and no default value is provided, an Error is raised.
    '''
    if isinstance(item, str):
        return _VARIABLE_PATTERN.sub(_resolve_string, item)
    if isinstance(item, list):
        for i, subitem in enumerate(item):
            item[i] = resolve_env_variables(subitem)
    if isinstance(item, dict):
        for key, value in item.items():
            item[key] = resolve_env_variables(value)
    return item
