import logging
import subprocess

import borgmatic.borg.info
import borgmatic.borg.recreate
import borgmatic.borg.repo_list
import borgmatic.config.validate
from borgmatic.actions.pattern import collect_patterns, process_patterns

logger = logging.getLogger(__name__)


BORG_EXIT_CODE_ARCHIVE_ALREADY_EXISTS = 30


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
            logger.answer(f'Recreating archive {recreate_arguments.archive}')
        else:
            logger.answer('Recreating repository')

        # Collect and process patterns.
        processed_patterns = process_patterns(
            collect_patterns(config), borgmatic.config.paths.get_working_directory(config)
        )

        archive = borgmatic.borg.repo_list.resolve_archive_name(
            repository['path'],
            recreate_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        )

        if archive and archive.endswith('.recreate'):
            if recreate_arguments.archive == 'latest':
                raise ValueError(
                    f'The latest archive "{archive}" is leftover from a prior recreate. Delete it first or select a different archive.'
                )
            else:
                raise ValueError(
                    f'The archive "{recreate_arguments.archive}" is leftover from a prior recreate. Select a different archive.'
                )

        try:
            borgmatic.borg.recreate.recreate_archive(
                repository['path'],
                archive,
                config,
                local_borg_version,
                recreate_arguments,
                global_arguments,
                local_path=local_path,
                remote_path=remote_path,
                patterns=processed_patterns,
            )
        except subprocess.CalledProcessError as error:
            if error.returncode == BORG_EXIT_CODE_ARCHIVE_ALREADY_EXISTS:
                if recreate_arguments.target:
                    raise ValueError(
                        f'The archive "{recreate_arguments.target}" already exists. Delete it first or set a different target archive name.'
                    )
                elif archive:
                    raise ValueError(
                        f'The archive "{archive}.recreate" is leftover from a prior recreate. Delete it first or select a different archive.'
                    )

            raise
