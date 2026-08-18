import logging

import borgmatic.borg.export_tar
import borgmatic.borg.repo_list

logger = logging.getLogger(__name__)


def run_export_tar(
    repository,
    config,
    local_borg_version,
    export_tar_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "export-tar" action for the given repository.
    '''
    logger.info(f'Exporting archive {export_tar_arguments.archive} as tar file')
    borgmatic.borg.export_tar.export_tar_archive(
        global_arguments.dry_run,
        repository['path'],
        borgmatic.borg.repo_list.resolve_archive_name(
            repository['path'],
            export_tar_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        ),
        export_tar_arguments.paths,
        export_tar_arguments.destination,
        config,
        local_borg_version,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
        tar_filter=export_tar_arguments.tar_filter,
        strip_components=export_tar_arguments.strip_components,
    )
