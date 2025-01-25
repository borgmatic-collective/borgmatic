import logging

import borgmatic.actions.arguments
import borgmatic.actions.json
import borgmatic.borg.list
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_list(
    repository,
    config,
    local_borg_version,
    list_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "list" action for the given repository and archive.

    If list_arguments.json is True, yield the JSON output from listing the archive.
    '''
    if list_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, list_arguments.repository
    ):
        if not list_arguments.json:
            if list_arguments.find_paths:  # pragma: no cover
                logger.answer('Searching archives')
            elif not list_arguments.archive:  # pragma: no cover
                logger.answer('Listing archives')

        archive_name = borgmatic.borg.repo_list.resolve_archive_name(
            repository['path'],
            list_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        )
        json_output = borgmatic.borg.list.list_archive(
            repository['path'],
            config,
            local_borg_version,
            borgmatic.actions.arguments.update_arguments(list_arguments, archive=archive_name),
            global_arguments,
            local_path,
            remote_path,
        )
        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))
