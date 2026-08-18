import logging

import borgmatic.borg.change_passphrase

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
    Run the "key change-passphrase" action for the given repository.
    '''
    logger.info('Changing repository passphrase')
    borgmatic.borg.change_passphrase.change_passphrase(
        repository['path'],
        config,
        local_borg_version,
        change_passphrase_arguments,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
    )
