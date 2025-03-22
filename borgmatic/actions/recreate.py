import logging

import borgmatic.borg.recreate
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_recreate(
    repository,
    config,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "recreate" action for the given repository.
    '''
    if recreate_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, recreate_arguments.repository
    ):
        if recreate_arguments.archive:
            logger.info(f'Recreating archive {recreate_arguments.archive}')
        else:
            logger.info('Recreating repository')

        borgmatic.borg.recreate.recreate_archive(
            repository['path'],
            borgmatic.borg.repo_list.resolve_archive_name(
                repository['path'],
                recreate_arguments.archive,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
            ),
            config,
            local_borg_version,
            recreate_arguments,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
