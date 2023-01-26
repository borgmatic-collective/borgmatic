import logging

import borgmatic.borg.break_lock
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_break_lock(
    repository, storage, local_borg_version, break_lock_arguments, local_path, remote_path,
):
    '''
    Run the "break-lock" action for the given repository.
    '''
    if break_lock_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, break_lock_arguments.repository
    ):
        logger.info(f'{repository}: Breaking repository and cache locks')
        borgmatic.borg.break_lock.break_lock(
            repository, storage, local_borg_version, local_path=local_path, remote_path=remote_path,
        )
