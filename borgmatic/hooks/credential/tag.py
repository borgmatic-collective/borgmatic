import functools

import borgmatic.hooks.dispatch

IS_A_HOOK = False


@functools.cache
def resolve_credential(tag):
    '''
    Given a configuration tag string like "!credential hookname credentialname", resolve it by
    calling the relevant hook to get the actual credential value. If the given tag is not actually a
    credential tag, then return the value unchanged.

    Cache the value so repeated calls to this function don't need to load the credential repeatedly.

    Raise ValueError if the config could not be parsed or the credential could not be loaded.
    '''
    if tag and tag.startswith('!credential '):
        try:
            (tag_name, hook_name, credential_name) = tag.split(' ', 2)
        except ValueError:
            raise ValueError(f'Cannot load credential with invalid syntax "{tag}"')

        return borgmatic.hooks.dispatch.call_hook(
            'load_credential', {}, hook_name, credential_name
        )

    return tag
