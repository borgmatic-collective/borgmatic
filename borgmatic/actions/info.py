import logging

import borgmatic.actions.arguments
import borgmatic.actions.json
import borgmatic.borg.info
import borgmatic.borg.repo_list
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_info(
    repository,
    config,
    local_borg_version,
    info_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "info" action for the given repository and archive.

    If info_arguments.json is True, yield the JSON output from the info for the archive.
    '''
    if info_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, info_arguments.repository
    ):
        if not info_arguments.json:
            logger.answer('Displaying archive summary information')
        archive_name = borgmatic.borg.repo_list.resolve_archive_name(
            repository['path'],
            info_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        )
        json_output = borgmatic.borg.info.display_archives_info(
            repository['path'],
            config,
            local_borg_version,
            borgmatic.actions.arguments.update_arguments(info_arguments, archive=archive_name),
            global_arguments,
            local_path,
            remote_path,
        )
        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))
