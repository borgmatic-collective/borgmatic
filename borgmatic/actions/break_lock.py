import logging

import borgmatic.borg.break_lock
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_break_lock(
    repository,
    config,
    local_borg_version,
    break_lock_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "break-lock" action for the given repository.
    '''
    if break_lock_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, break_lock_arguments.repository
    ):
        logger.info('Breaking repository and cache locks')
        borgmatic.borg.break_lock.break_lock(
            repository['path'],
            config,
            local_borg_version,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
