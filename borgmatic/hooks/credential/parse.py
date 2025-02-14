import functools
import re
import shlex

import borgmatic.hooks.dispatch

IS_A_HOOK = False


CREDENTIAL_PATTERN = re.compile(r'\{credential( +(?P<hook_and_parameters>.*))?\}')


@functools.cache
def resolve_credential(value):
    '''
    Given a configuration value containing a string like "{credential hookname credentialname}", resolve it by
    calling the relevant hook to get the actual credential value. If the given value does not
    actually contain a credential tag, then return it unchanged.

    Cache the value so repeated calls to this function don't need to load the credential repeatedly.

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
        'load_credential', {}, hook_name, tuple(credential_parameters)
    )
