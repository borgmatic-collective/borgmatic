import logging

import borgmatic.actions.json
import borgmatic.borg.repo_list
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_repo_list(
    repository,
    config,
    local_borg_version,
    repo_list_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "repo-list" action for the given repository.

    If repo_list_arguments.json is True, yield the JSON output from listing the repository.
    '''
    if repo_list_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, repo_list_arguments.repository
    ):
        if not repo_list_arguments.json:
            logger.answer('Listing repository')

        json_output = borgmatic.borg.repo_list.list_repository(
            repository['path'],
            config,
            local_borg_version,
            repo_list_arguments=repo_list_arguments,
            global_arguments=global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))
