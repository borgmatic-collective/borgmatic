import logging

import borgmatic.actions.json
import borgmatic.borg.rlist
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_rlist(
    repository,
    config,
    local_borg_version,
    rlist_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "rlist" action for the given repository.

    If rlist_arguments.json is True, yield the JSON output from listing the repository.
    '''
    if rlist_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, rlist_arguments.repository
    ):
        if not rlist_arguments.json:
            logger.answer(f'{repository.get("label", repository["path"])}: Listing repository')

        json_output = borgmatic.borg.rlist.list_repository(
            repository['path'],
            config,
            local_borg_version,
            rlist_arguments=rlist_arguments,
            global_arguments=global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))
