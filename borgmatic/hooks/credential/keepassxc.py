import logging
import os
import shlex

import borgmatic.execute

logger = logging.getLogger(__name__)


def load_credential(hook_config, config, credential_parameters):
    '''
    Given the hook configuration dict, the configuration dict, and a credential parameters tuple
    containing a KeePassXC database path and an attribute name to load, run keepassxc-cli to fetch
    the corresponidng KeePassXC credential and return it.

    Raise ValueError if keepassxc-cli can't retrieve the credential.
    '''
    try:
        (database_path, attribute_name) = credential_parameters
    except ValueError:
        raise ValueError(
            f'Cannot load credential with invalid KeePassXC database path and attribute name: "{' '.join(credential_parameters)}"'
        )

    if not os.path.exists(database_path):
        raise ValueError(
            f'Cannot load credential because KeePassXC database path does not exist: {database_path}'
        )

    return borgmatic.execute.execute_command_and_capture_output(
        tuple(shlex.split((hook_config or {}).get('keepassxc_cli_command', 'keepassxc-cli')))
        + (
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            database_path,
            attribute_name,
        )
    ).rstrip(os.linesep)
