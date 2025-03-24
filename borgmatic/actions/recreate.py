import logging

import borgmatic.borg.recreate
import borgmatic.config.validate
from borgmatic.actions.create import collect_patterns, process_patterns

logger = logging.getLogger(__name__)


def run_recreate(
    repository,
    config,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "recreate" action for the given repository.
    '''
    if recreate_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, recreate_arguments.repository
    ):
        if recreate_arguments.archive:
            logger.info(f'Recreating archive {recreate_arguments.archive}')
        else:
            logger.info('Recreating repository')

        # collect and process patterns
        patterns = collect_patterns(config)
        processed_patterns = process_patterns(
            patterns, borgmatic.config.paths.get_working_directory(config)
        )

        borgmatic.borg.recreate.recreate_archive(
            repository['path'],
            borgmatic.borg.repo_list.resolve_archive_name(
                repository['path'],
                recreate_arguments.archive,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
            ),
            config,
            local_borg_version,
            recreate_arguments,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
            patterns=processed_patterns,
        )
