import json
import logging

import borgmatic.borg.rlist
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_rlist(
    repository, storage, local_borg_version, rlist_arguments, local_path, remote_path,
):
    '''
    Run the "rlist" action for the given repository.

    If rlist_arguments.json is True, yield the JSON output from listing the repository.
    '''
    if rlist_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, rlist_arguments.repository
    ):
        if not rlist_arguments.json:  # pragma: nocover
            logger.answer('{}: Listing repository'.format(repository))
        json_output = borgmatic.borg.rlist.list_repository(
            repository,
            storage,
            local_borg_version,
            rlist_arguments=rlist_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:  # pragma: nocover
            yield json.loads(json_output)
