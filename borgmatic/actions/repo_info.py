import logging

import borgmatic.actions.json
import borgmatic.borg.repo_info
import borgmatic.config.validate

logger = logging.getLogger(__name__)


def run_repo_info(
    repository,
    config,
    local_borg_version,
    repo_info_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "repo-info" action for the given repository.

    If repo_info_arguments.json is True, yield the JSON output from the info for the repository.
    '''
    if repo_info_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, repo_info_arguments.repository
    ):
        if not repo_info_arguments.json:
            logger.answer('Displaying repository summary information')

        json_output = borgmatic.borg.repo_info.display_repository_info(
            repository['path'],
            config,
            local_borg_version,
            repo_info_arguments=repo_info_arguments,
            global_arguments=global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))
