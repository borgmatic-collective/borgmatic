import functools
import re
import shlex

import borgmatic.hooks.dispatch

IS_A_HOOK = False


class Hash_adapter:
    '''
    A Hash_adapter instance wraps an unhashable object and pretends it's hashable. This is intended
    for passing to a @functools.cache-decorated function to prevent it from complaining that an
    argument is unhashable. It should only be used for arguments that you don't want to actually
    impact the cache hashing, because Hash_adapter doesn't actually hash the object's contents.

    Example usage:

        @functools.cache
        def func(a, b):
            print(a, b.actual_value)
            return a

        func(5, Hash_adapter({1: 2, 3: 4}))  # Calls func(), prints, and returns.
        func(5, Hash_adapter({1: 2, 3: 4}))  # Hits the cache and just returns the value.
        func(5, Hash_adapter({5: 6, 7: 8}))  # Also uses cache, since the Hash_adapter is ignored.

    In the above function, the "b" value is one that has been wrapped with Hash_adappter, and
    therefore "b.actual_value" is necessary to access the original value.
    '''

    def __init__(self, actual_value):
        self.actual_value = actual_value

    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


UNHASHABLE_TYPES = (dict, list, set)


def cache_ignoring_unhashable_arguments(function):
    '''
    A function decorator that caches calls to the decorated function but ignores any unhashable
    arguments when performing cache lookups. This is intended to be a drop-in replacement for
    functools.cache.

    Example usage:

        @cache_ignoring_unhashable_arguments
        def func(a, b):
            print(a, b)
            return a

        func(5, {1: 2, 3: 4})  # Calls func(), prints, and returns.
        func(5, {1: 2, 3: 4})  # Hits the cache and just returns the value.
        func(5, {5: 6, 7: 8})  # Also uses cache, since the unhashable value (the dict) is ignored.
    '''

    @functools.cache
    def cached_function(*args, **kwargs):
        return function(
            *(arg.actual_value if isinstance(arg, Hash_adapter) else arg for arg in args),
            **{
                key: value.actual_value if isinstance(value, Hash_adapter) else value
                for (key, value) in kwargs.items()
            },
        )

    @functools.wraps(function)
    def wrapper_function(*args, **kwargs):
        return cached_function(
            *(Hash_adapter(arg) if isinstance(arg, UNHASHABLE_TYPES) else arg for arg in args),
            **{
                key: Hash_adapter(value) if isinstance(value, UNHASHABLE_TYPES) else value
                for (key, value) in kwargs.items()
            },
        )

    wrapper_function.cache_clear = cached_function.cache_clear

    return wrapper_function


CREDENTIAL_PATTERN = re.compile(r'\{credential( +(?P<hook_and_parameters>.*))?\}')


@cache_ignoring_unhashable_arguments
def resolve_credential(value, config):
    '''
    Given a configuration value containing a string like "{credential hookname credentialname}" and
    a configuration dict, resolve the credential by calling the relevant hook to get the actual
    credential value. If the given value does not actually contain a credential tag, then return it
    unchanged.

    Cache the value (ignoring the config for purposes of caching), so repeated calls to this
    function don't need to load the credential repeatedly.

    Raise ValueError if the config could not be parsed or the credential could not be loaded.
    '''
    if value is None:
        return value

    matcher = CREDENTIAL_PATTERN.match(value)

    if not matcher:
        return value

    hook_and_parameters = matcher.group('hook_and_parameters')

    if not hook_and_parameters:
        raise ValueError(f'Cannot load credential with invalid syntax "{value}"')

    (hook_name, *credential_parameters) = shlex.split(hook_and_parameters)

    if not credential_parameters:
        raise ValueError(f'Cannot load credential with invalid syntax "{value}"')

    return borgmatic.hooks.dispatch.call_hook(
        'load_credential', config, hook_name, tuple(credential_parameters)
    )
