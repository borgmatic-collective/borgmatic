import logging

import borgmatic.borg.rdelete

logger = logging.getLogger(__name__)


def run_rdelete(
    repository,
    config,
    local_borg_version,
    rdelete_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "rdelete" action for the given repository.
    '''
    if rdelete_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, rdelete_arguments.repository
    ):
        logger.answer(f'{repository.get("label", repository["path"])}: Deleting repository')

        borgmatic.borg.rdelete.delete_repository(
            repository,
            config,
            local_borg_version,
            rdelete_arguments,
            global_arguments,
            local_path,
            remote_path,
        )
