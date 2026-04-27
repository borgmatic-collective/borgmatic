import logging

import borgmatic.actions.pattern
import borgmatic.borg.diff

logger = logging.getLogger(__name__)


def run_diff(
    repository,
    config,
    local_borg_version,
    diff_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "diff" action for the given repository.
    '''

    # Only process patterns if only_patterns flag is set
    if diff_arguments.only_patterns:
        working_directory = borgmatic.config.paths.get_working_directory(config)
        processed_patterns = borgmatic.actions.pattern.process_patterns(
            (*borgmatic.actions.pattern.collect_patterns(config, working_directory),),
            config,
            working_directory,
        )
    else:
        processed_patterns = None

    archive = borgmatic.borg.repo_list.resolve_archive_name(
        repository['path'],
        diff_arguments.archive,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
    )
    second_archive = borgmatic.borg.repo_list.resolve_archive_name(
        repository['path'],
        diff_arguments.second_archive,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
    )

    borgmatic.borg.diff.diff(
        repository['path'],
        archive,
        second_archive,
        config,
        local_borg_version,
        diff_arguments,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
        patterns=processed_patterns,
    )
