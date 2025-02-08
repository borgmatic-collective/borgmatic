import borgmatic.hooks.dispatch


def resolve_credentials(config, item=None):
    '''
    Resolves values like "!credential hookname credentialname" from the given configuration by
    calling relevant hooks to get the actual credential values. The item parameter is used to
    support recursing through the config hierarchy; it represents the current piece of config being
    looked at.

    Raise ValueError if the config could not be parsed or the credential could not be loaded.
    '''
    if not item:
        item = config

    if isinstance(item, str):
        if item.startswith('!credential '):
            try:
                (tag_name, hook_name, credential_name) = item.split(' ', 2)
            except ValueError:
                raise ValueError(f'Cannot load credential with invalid syntax "{item}"')

            return borgmatic.hooks.dispatch.call_hook(
                'load_credential', config, hook_name, credential_name
            )

    if isinstance(item, list):
        for index, subitem in enumerate(item):
            item[index] = resolve_credentials(config, subitem)

    if isinstance(item, dict):
        for key, value in item.items():
            item[key] = resolve_credentials(config, value)

    return item
