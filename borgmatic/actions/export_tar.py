import logging

import borgmatic.borg.export_tar
import borgmatic.borg.rlist
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_export_tar(
    repository,
    storage,
    local_borg_version,
    export_tar_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "export-tar" action for the given repository.
    '''
    if export_tar_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, export_tar_arguments.repository
    ):
        logger.info(
            '{}: Exporting archive {} as tar file'.format(repository, export_tar_arguments.archive)
        )
        borgmatic.borg.export_tar.export_tar_archive(
            global_arguments.dry_run,
            repository,
            borgmatic.borg.rlist.resolve_archive_name(
                repository,
                export_tar_arguments.archive,
                storage,
                local_borg_version,
                local_path,
                remote_path,
            ),
            export_tar_arguments.paths,
            export_tar_arguments.destination,
            storage,
            local_borg_version,
            local_path=local_path,
            remote_path=remote_path,
            tar_filter=export_tar_arguments.tar_filter,
            list_files=export_tar_arguments.list_files,
            strip_components=export_tar_arguments.strip_components,
        )
