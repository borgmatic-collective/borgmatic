import json
import logging

import borgmatic.borg.info
import borgmatic.borg.rlist
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_info(
    repository, storage, local_borg_version, info_arguments, local_path, remote_path,
):
    '''
    Run the "info" action for the given repository and archive.

    If info_arguments.json is True, yield the JSON output from the info for the archive.
    '''
    if info_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, info_arguments.repository
    ):
        if not info_arguments.json:  # pragma: nocover
            logger.answer(f'{repository}: Displaying archive summary information')
        info_arguments.archive = borgmatic.borg.rlist.resolve_archive_name(
            repository,
            info_arguments.archive,
            storage,
            local_borg_version,
            local_path,
            remote_path,
        )
        json_output = borgmatic.borg.info.display_archives_info(
            repository,
            storage,
            local_borg_version,
            info_arguments=info_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:  # pragma: nocover
            yield json.loads(json_output)
