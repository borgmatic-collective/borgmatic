import logging

import borgmatic.borg.change_passphrase
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_change_passphrase(
    repository,
    config,
    local_borg_version,
    change_passphrase_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "key change-passprhase" action for the given repository.
    '''
    if (
        change_passphrase_arguments.repository is None
        or borgmatic.config.validate.repositories_match(
            repository, change_passphrase_arguments.repository
        )
    ):
        logger.info(
            f'{repository.get("label", repository["path"])}: Changing repository passphrase'
        )
        borgmatic.borg.change_passphrase.change_passphrase(
            repository['path'],
            config,
            local_borg_version,
            change_passphrase_arguments,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
