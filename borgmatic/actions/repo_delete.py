import logging

import borgmatic.borg.repo_delete

logger = logging.getLogger(__name__)


def run_repo_delete(
    repository,
    config,
    local_borg_version,
    repo_delete_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "repo-delete" action for the given repository.
    '''
    if repo_delete_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, repo_delete_arguments.repository
    ):
        logger.answer(
            'Deleting repository' + (' cache' if repo_delete_arguments.cache_only else '')
        )

        borgmatic.borg.repo_delete.delete_repository(
            repository,
            config,
            local_borg_version,
            repo_delete_arguments,
            global_arguments,
            local_path,
            remote_path,
        )
