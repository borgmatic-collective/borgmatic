import logging

import borgmatic.borg.import_key
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_import_key(
    repository,
    config,
    local_borg_version,
    import_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "key import" action for the given repository.
    '''
    if import_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, import_arguments.repository
    ):
        logger.info('Importing repository key')
        borgmatic.borg.import_key.import_key(
            repository['path'],
            config,
            local_borg_version,
            import_arguments,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
