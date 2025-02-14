import logging
import os

logger = logging.getLogger(__name__)


def load_credential(hook_config, config, credential_parameters):
    '''
    Given the hook configuration dict, the configuration dict, and a credential parameters tuple
    containing a credential path to load, load the credential from file and return it.

    Raise ValueError if the credential parameters is not one element or the secret file cannot be
    read.
    '''
    try:
        (credential_path,) = credential_parameters
    except ValueError:
        raise ValueError(f'Cannot load invalid credential: "{' '.join(credential_parameters)}"')

    try:
        with open(credential_path) as credential_file:
            return credential_file.read().rstrip(os.linesep)
    except (FileNotFoundError, OSError) as error:
        logger.warning(error)

        raise ValueError(f'Cannot load credential file: {error.filename}')
