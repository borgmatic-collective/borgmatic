import logging

import borgmatic.borg.import_key

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
