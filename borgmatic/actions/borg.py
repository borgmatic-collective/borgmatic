import logging

import borgmatic.borg.borg
import borgmatic.borg.repo_list

logger = logging.getLogger(__name__)


def run_borg(
    repository,
    config,
    local_borg_version,
    borg_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "borg" action for the given repository.
    '''
    logger.info('Running arbitrary Borg command')
    archive_name = borgmatic.borg.repo_list.resolve_archive_name(
        repository['path'],
        borg_arguments.archive,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
    )
    borgmatic.borg.borg.run_arbitrary_borg(
        repository['path'],
        config,
        local_borg_version,
        options=borg_arguments.options,
        archive=archive_name,
        local_path=local_path,
        remote_path=remote_path,
    )
