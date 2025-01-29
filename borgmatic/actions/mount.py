import logging

import borgmatic.borg.mount
import borgmatic.borg.repo_list
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_mount(
    repository,
    config,
    local_borg_version,
    mount_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "mount" action for the given repository.
    '''
    if mount_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, mount_arguments.repository
    ):
        if mount_arguments.archive:
            logger.info(f'Mounting archive {mount_arguments.archive}')
        else:  # pragma: nocover
            logger.info('Mounting repository')

        borgmatic.borg.mount.mount_archive(
            repository['path'],
            borgmatic.borg.repo_list.resolve_archive_name(
                repository['path'],
                mount_arguments.archive,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
            ),
            mount_arguments,
            config,
            local_borg_version,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
