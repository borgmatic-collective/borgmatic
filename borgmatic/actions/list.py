import json
import logging

import borgmatic.borg.list
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_list(
    repository, storage, local_borg_version, list_arguments, local_path, remote_path,
):
    '''
    Run the "list" action for the given repository and archive.

    If list_arguments.json is True, yield the JSON output from listing the archive.
    '''
    if list_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, list_arguments.repository
    ):
        if not list_arguments.json:  # pragma: nocover
            if list_arguments.find_paths:
                logger.answer(f'{repository}: Searching archives')
            elif not list_arguments.archive:
                logger.answer(f'{repository}: Listing archives')
        list_arguments.archive = borgmatic.borg.rlist.resolve_archive_name(
            repository,
            list_arguments.archive,
            storage,
            local_borg_version,
            local_path,
            remote_path,
        )
        json_output = borgmatic.borg.list.list_archive(
            repository,
            storage,
            local_borg_version,
            list_arguments=list_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:  # pragma: nocover
            yield json.loads(json_output)
