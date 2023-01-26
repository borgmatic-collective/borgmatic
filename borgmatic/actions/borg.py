import logging

import borgmatic.borg.borg
import borgmatic.borg.rlist
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_borg(
    repository, storage, local_borg_version, borg_arguments, local_path, remote_path,
):
    '''
    Run the "borg" action for the given repository.
    '''
    if borg_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, borg_arguments.repository
    ):
        logger.info('{}: Running arbitrary Borg command'.format(repository))
        archive_name = borgmatic.borg.rlist.resolve_archive_name(
            repository,
            borg_arguments.archive,
            storage,
            local_borg_version,
            local_path,
            remote_path,
        )
        borgmatic.borg.borg.run_arbitrary_borg(
            repository,
            storage,
            local_borg_version,
            options=borg_arguments.options,
            archive=archive_name,
            local_path=local_path,
            remote_path=remote_path,
        )
