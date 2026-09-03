import logging
import os
import shlex

import borgmatic.execute

logger = logging.getLogger(__name__)


SECRET_REFERENCE_PREFIX = 'op://'


def load_credential(hook_config, config, credential_parameters):
    '''
    Given the hook configuration dict, the configuration dict, and a credential parameters tuple
    containing a 1Password secret reference to load, run the 1Password CLI to fetch the
    corresponding credential and return it.

    Raise ValueError if the credential parameters are not one element or the secret reference is
    invalid.
    '''
    try:
        (secret_reference,) = credential_parameters
    except ValueError:
        name = ' '.join(credential_parameters)

        raise ValueError(f'Cannot load invalid credential: "{name}"')

    if not secret_reference.startswith(SECRET_REFERENCE_PREFIX):
        raise ValueError(f'Cannot load invalid 1Password secret reference: "{secret_reference}"')

    command = (
        *shlex.split((hook_config or {}).get('op_command', 'op')),
        'read',
        '--no-newline',
        secret_reference,
    )

    return '\n'.join(borgmatic.execute.execute_command_and_capture_output(command)).rstrip(
        os.linesep
    )
