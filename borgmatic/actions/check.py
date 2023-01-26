import logging

import borgmatic.borg.check
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
    borgmatic.hooks.command.execute_hook(
        hooks.get('before_check'),
        hooks.get('umask'),
        config_filename,
        'pre-check',
        global_arguments.dry_run,
        **hook_context,
    )
    logger.info('{}: Running consistency checks'.format(repository))
    borgmatic.borg.check.check_archives(
        repository,
        location,
        storage,
        consistency,
        local_borg_version,
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
