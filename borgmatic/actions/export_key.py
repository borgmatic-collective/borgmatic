import logging

import borgmatic.borg.export_key
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_export_key(
    repository,
    config,
    local_borg_version,
    export_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "key export" action for the given repository.
    '''
    if export_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, export_arguments.repository
    ):
        logger.info('Exporting repository key')
        borgmatic.borg.export_key.export_key(
            repository['path'],
            config,
            local_borg_version,
            export_arguments,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
