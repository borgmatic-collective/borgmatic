import logging
import subprocess

import borgmatic.actions.pattern
import borgmatic.borg.pattern
import borgmatic.borg.recreate
import borgmatic.borg.repo_list

logger = logging.getLogger(__name__)


BORG_EXIT_CODE_ARCHIVE_ALREADY_EXISTS = 30


def run_recreate(
    repository,
    config,
    local_borg_version,
    recreate_arguments,
    global_arguments,
    dry_run_label,
    local_path,
    remote_path,
):
    '''
    Run the "recreate" action for the given repository.
    '''
    if recreate_arguments.archive:
        logger.answer(f'Recreating archive {recreate_arguments.archive}{dry_run_label}')
    else:
        logger.answer(f'Recreating repository{dry_run_label}')

    # Collect and process patterns.
    processed_patterns = borgmatic.actions.pattern.process_patterns(
        (
            *borgmatic.actions.pattern.collect_patterns(config),
            # Also add borgmatic-specific paths, so they don't get excluded from the recreated
            # archive. Note that this doesn't currently work for archives created with Borg 1.2 or
            # below.
            borgmatic.borg.pattern.Pattern(
                '/borgmatic', source=borgmatic.borg.pattern.Pattern_source.INTERNAL
            ),
        ),
        config,
        borgmatic.config.paths.get_working_directory(config),
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
                f'The latest archive "{archive}" is leftover from a prior recreate. Delete it first or select a different archive.',
            )

        raise ValueError(
            f'The archive "{recreate_arguments.archive}" is leftover from a prior recreate. Select a different archive.',
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
                    f'The archive "{recreate_arguments.target}" already exists. Delete it first or set a different target archive name.',
                )

            if archive:
                raise ValueError(
                    f'The archive "{archive}.recreate" is leftover from a prior recreate. Delete it first or select a different archive.',
                )

        raise
