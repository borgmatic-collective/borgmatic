import logging

import borgmatic.borg.check
import borgmatic.config.validate
import borgmatic.hooks.command

logger = logging.getLogger(__name__)


def run_check(
    config_filename,
    repository,
    location,
    storage,
    consistency,
    hooks,
    hook_context,
    local_borg_version,
    check_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "check" action for the given repository.
    '''
    if check_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, check_arguments.repository
    ):
        return

    borgmatic.hooks.command.execute_hook(
        hooks.get('before_check'),
        hooks.get('umask'),
        config_filename,
        'pre-check',
        global_arguments.dry_run,
        **hook_context,
    )
    logger.info(f'{repository.get("label", repository["path"])}: Running consistency checks')
    borgmatic.borg.check.check_archives(
        repository['path'],
        location,
        storage,
        consistency,
        local_borg_version,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
        progress=check_arguments.progress,
        repair=check_arguments.repair,
        only_checks=check_arguments.only,
        force=check_arguments.force,
    )
    borgmatic.hooks.command.execute_hook(
        hooks.get('after_check'),
        hooks.get('umask'),
        config_filename,
        'post-check',
        global_arguments.dry_run,
        **hook_context,
    )
