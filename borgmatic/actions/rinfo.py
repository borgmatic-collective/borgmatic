import json
import logging

import borgmatic.borg.rinfo
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_rinfo(
    repository, storage, local_borg_version, rinfo_arguments, local_path, remote_path,
):
    '''
    Run the "rinfo" action for the given repository.

    If rinfo_arguments.json is True, yield the JSON output from the info for the repository.
    '''
    if rinfo_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, rinfo_arguments.repository
    ):
        if not rinfo_arguments.json:  # pragma: nocover
            logger.answer('{}: Displaying repository summary information'.format(repository))
        json_output = borgmatic.borg.rinfo.display_repository_info(
            repository,
            storage,
            local_borg_version,
            rinfo_arguments=rinfo_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:  # pragma: nocover
            yield json.loads(json_output)
