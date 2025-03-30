import logging
import os
import shlex

import borgmatic.execute

logger = logging.getLogger(__name__)


def load_credential(hook_config, config, credential_parameters):
    '''
    Given the hook configuration dict, the configuration dict, and a credential parameters tuple
    containing a KeePassXC database path and an attribute name to load, run keepassxc-cli to fetch
    the corresponding KeePassXC credential and return it.

    Raise ValueError if keepassxc-cli can't retrieve the credential.
    '''
    try:
        database_path, attribute_name = credential_parameters[:2]
        extra_args = credential_parameters[2:]  # Handle additional arguments like --key-file or --yubikey
    except ValueError:
        raise ValueError( f'Invalid KeePassXC credential parameters: {credential_parameters}')

    expanded_database_path = os.path.expanduser(database_path)

    if not os.path.exists(expanded_database_path):
        raise ValueError( f'KeePassXC database path does not exist: {database_path}')

    # Build the keepassxc-cli command
    command = (
        tuple(shlex.split((hook_config or {}).get('keepassxc_cli_command', 'keepassxc-cli')))
        + (
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            expanded_database_path,
            attribute_name,
        )
        + tuple(extra_args)  # Append extra arguments
    )

    try:
        return borgmatic.execute.execute_command_and_capture_output(command).rstrip(os.linesep)
    except Exception as e:
        raise ValueError(f'Failed to retrieve credential: {e}')
