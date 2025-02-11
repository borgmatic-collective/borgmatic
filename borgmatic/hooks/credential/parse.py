import functools
import re

import borgmatic.hooks.dispatch

IS_A_HOOK = False


CREDENTIAL_PATTERN = re.compile(
    r'\{credential +(?P<hook_name>[A-Za-z0-9_]+) +(?P<credential_name>[A-Za-z0-9_]+)\}'
)

GENERAL_CREDENTIAL_PATTERN = re.compile(r'\{credential( +[^}]*)?\}')


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

    result = CREDENTIAL_PATTERN.sub(
        lambda matcher: borgmatic.hooks.dispatch.call_hook(
            'load_credential', {}, matcher.group('hook_name'), matcher.group('credential_name')
        ),
        value,
    )

    # If we've tried to parse the credential, but the parsed result still looks kind of like a
    # credential, it means it's invalid syntax.
    if GENERAL_CREDENTIAL_PATTERN.match(result):
        raise ValueError(f'Cannot load credential with invalid syntax "{value}"')

    return result
