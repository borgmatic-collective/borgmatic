import logging
import os
import re

logger = logging.getLogger(__name__)


CREDENTIAL_NAME_PATTERN = re.compile(r'^[\w.-]+$')


def load_credential(hook_config, config, credential_parameters):
    '''
    Given the hook configuration dict, the configuration dict, and a credential parameters tuple
    containing a credential name to load, read the credential from the corresponding systemd
    credential file and return it.

    Raise ValueError if the systemd CREDENTIALS_DIRECTORY environment variable is not set, the
    credential name is invalid, or the credential file cannot be read.
    '''
    try:
        (credential_name,) = credential_parameters
    except ValueError:
        name = ' '.join(credential_parameters)

        raise ValueError(f'Cannot load invalid credential name: "{name}"')

    credentials_directory = os.environ.get('CREDENTIALS_DIRECTORY')

    if not credentials_directory:
        raise ValueError(
            f'Cannot load credential "{credential_name}" because the systemd CREDENTIALS_DIRECTORY environment variable is not set'
        )

    if not CREDENTIAL_NAME_PATTERN.match(credential_name):
        raise ValueError(f'Cannot load invalid credential name "{credential_name}"')

    try:
        with open(os.path.join(credentials_directory, credential_name)) as credential_file:
            return credential_file.read().rstrip(os.linesep)
    except (FileNotFoundError, OSError) as error:
        logger.warning(error)

        raise ValueError(f'Cannot load credential "{credential_name}" from file: {error.filename}')
