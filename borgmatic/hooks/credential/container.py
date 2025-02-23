import logging
import os
import re

logger = logging.getLogger(__name__)


SECRET_NAME_PATTERN = re.compile(r'^\w+$')
DEFAULT_SECRETS_DIRECTORY = '/run/secrets'


def load_credential(hook_config, config, credential_parameters):
    '''
    Given the hook configuration dict, the configuration dict, and a credential parameters tuple
    containing a secret name to load, read the secret from the corresponding container secrets file
    and return it.

    Raise ValueError if the credential parameters is not one element, the secret name is invalid, or
    the secret file cannot be read.
    '''
    try:
        (secret_name,) = credential_parameters
    except ValueError:
        name = ' '.join(credential_parameters)

        raise ValueError(f'Cannot load invalid secret name: "{name}"')

    if not SECRET_NAME_PATTERN.match(secret_name):
        raise ValueError(f'Cannot load invalid secret name: "{secret_name}"')

    try:
        with open(
            os.path.join(
                config.get('working_directory', ''),
                (hook_config or {}).get('secrets_directory', DEFAULT_SECRETS_DIRECTORY),
                secret_name,
            )
        ) as secret_file:
            return secret_file.read().rstrip(os.linesep)
    except (FileNotFoundError, OSError) as error:
        logger.warning(error)

        raise ValueError(f'Cannot load secret "{secret_name}" from file: {error.filename}')
