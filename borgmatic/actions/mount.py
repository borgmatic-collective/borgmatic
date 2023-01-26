import logging

import borgmatic.borg.mount
import borgmatic.borg.rlist
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_mount(
    repository, storage, local_borg_version, mount_arguments, local_path, remote_path,
):
    '''
    Run the "mount" action for the given repository.
    '''
    if mount_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, mount_arguments.repository
    ):
        if mount_arguments.archive:
            logger.info('{}: Mounting archive {}'.format(repository, mount_arguments.archive))
        else:  # pragma: nocover
            logger.info('{}: Mounting repository'.format(repository))

        borgmatic.borg.mount.mount_archive(
            repository,
            borgmatic.borg.rlist.resolve_archive_name(
                repository,
                mount_arguments.archive,
                storage,
                local_borg_version,
                local_path,
                remote_path,
            ),
            mount_arguments.mount_point,
            mount_arguments.paths,
            mount_arguments.foreground,
            mount_arguments.options,
            storage,
            local_borg_version,
            local_path=local_path,
            remote_path=remote_path,
        )
