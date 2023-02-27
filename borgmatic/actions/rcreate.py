import logging

import borgmatic.borg.rcreate
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_rcreate(
    repository,
    storage,
    local_borg_version,
    rcreate_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "rcreate" action for the given repository.
    '''
    if rcreate_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, rcreate_arguments.repository
    ):
        return

    logger.info('{}: Creating repository'.format(repository))
    borgmatic.borg.rcreate.create_repository(
        global_arguments.dry_run,
        repository,
        storage,
        local_borg_version,
        rcreate_arguments.encryption_mode,
        rcreate_arguments.source_repository,
        rcreate_arguments.copy_crypt_key,
        rcreate_arguments.append_only,
        rcreate_arguments.storage_quota,
        rcreate_arguments.make_parent_dirs,
        local_path=local_path,
        remote_path=remote_path,
    )
