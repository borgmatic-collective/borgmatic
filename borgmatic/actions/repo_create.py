import logging

import borgmatic.borg.repo_create

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
    logger.info('Creating repository')

    encryption_mode = repo_create_arguments.encryption_mode or repository.get('encryption')

    if not encryption_mode:
        raise ValueError(
            'With the repo-create action, either the --encryption flag or the repository encryption option is required.',
        )

    borgmatic.borg.repo_create.create_repository(
        dry_run=global_arguments.dry_run,
        repository_path=repository['path'],
        config=config,
        local_borg_version=local_borg_version,
        global_arguments=global_arguments,
        encryption_mode=encryption_mode,
        id_hash=(
            repository.get('id_hash')
            if repo_create_arguments.id_hash is None
            else repo_create_arguments.id_hash
        ),
        key_location=(
            repository.get('key_location')
            if repo_create_arguments.key_location is None
            else repo_create_arguments.key_location
        ),
        source_repository=repo_create_arguments.source_repository,
        from_borg1=repo_create_arguments.from_borg1,
        copy_crypt_key=repo_create_arguments.copy_crypt_key,
        append_only=(
            repository.get('append_only')
            if repo_create_arguments.append_only is None
            else repo_create_arguments.append_only
        ),
        storage_quota=(
            repository.get('storage_quota')
            if repo_create_arguments.storage_quota is None
            else repo_create_arguments.storage_quota
        ),
        make_parent_directories=(
            repository.get('make_parent_directories')
            if repo_create_arguments.make_parent_directories is None
            else repo_create_arguments.make_parent_directories
        ),
        local_path=local_path,
        remote_path=remote_path,
    )
