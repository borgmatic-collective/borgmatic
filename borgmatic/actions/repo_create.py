import logging

import borgmatic.borg.repo_create
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_repo_create(
    repository,
    config,
    local_borg_version,
    repo_create_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "repo-create" action for the given repository.
    '''
    if repo_create_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, repo_create_arguments.repository
    ):
        return

    logger.info('Creating repository')

    encryption_mode = repo_create_arguments.encryption_mode or repository.get('encryption')

    if not encryption_mode:
        raise ValueError(
            'With the repo-create action, either the --encryption flag or the repository encryption option is required.'
        )

    borgmatic.borg.repo_create.create_repository(
        global_arguments.dry_run,
        repository['path'],
        config,
        local_borg_version,
        global_arguments,
        encryption_mode,
        repo_create_arguments.source_repository,
        repo_create_arguments.copy_crypt_key,
        (
            repository.get('append_only')
            if repo_create_arguments.append_only is None
            else repo_create_arguments.append_only
        ),
        (
            repository.get('storage_quota')
            if repo_create_arguments.storage_quota is None
            else repo_create_arguments.storage_quota
        ),
        (
            repository.get('make_parent_directories')
            if repo_create_arguments.make_parent_directories is None
            else repo_create_arguments.make_parent_directories
        ),
        local_path=local_path,
        remote_path=remote_path,
    )
