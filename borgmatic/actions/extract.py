import logging

import borgmatic.borg.extract
import borgmatic.borg.repo_list
import borgmatic.config.validate
import borgmatic.hooks.command

logger = logging.getLogger(__name__)


def run_extract(
    config_filename,
    repository,
    config,
    hook_context,
    local_borg_version,
    extract_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "extract" action for the given repository.
    '''
    borgmatic.hooks.command.execute_hook(
        config.get('before_extract'),
        config.get('umask'),
        config_filename,
        'pre-extract',
        global_arguments.dry_run,
        **hook_context,
    )
    if extract_arguments.repository is None or borgmatic.config.validate.repositories_match(
        repository, extract_arguments.repository
    ):
        logger.info(
            f'{repository.get("label", repository["path"])}: Extracting archive {extract_arguments.archive}'
        )
        borgmatic.borg.extract.extract_archive(
            global_arguments.dry_run,
            repository['path'],
            borgmatic.borg.repo_list.resolve_archive_name(
                repository['path'],
                extract_arguments.archive,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
            ),
            extract_arguments.paths,
            config,
            local_borg_version,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
            destination_path=extract_arguments.destination,
            strip_components=extract_arguments.strip_components,
            progress=extract_arguments.progress,
        )
    borgmatic.hooks.command.execute_hook(
        config.get('after_extract'),
        config.get('umask'),
        config_filename,
        'post-extract',
        global_arguments.dry_run,
        **hook_context,
    )
