import logging

import borgmatic.actions.arguments
import borgmatic.borg.delete
import borgmatic.borg.repo_delete
import borgmatic.borg.repo_list

logger = logging.getLogger(__name__)


def run_delete(
    repository,
    config,
    local_borg_version,
    delete_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "delete" action for the given repository and archive(s).
    '''
    logger.answer('Deleting archives')

    archive_name = (
        borgmatic.borg.repo_list.resolve_archive_name(
            repository['path'],
            delete_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        )
        if delete_arguments.archive
        else None
    )

    borgmatic.borg.delete.delete_archives(
        repository,
        config,
        local_borg_version,
        borgmatic.actions.arguments.update_arguments(delete_arguments, archive=archive_name),
        global_arguments,
        local_path,
        remote_path,
    )
