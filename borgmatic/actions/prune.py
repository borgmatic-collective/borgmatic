import logging

import borgmatic.borg.prune
import borgmatic.config.validate
import borgmatic.hooks.command

logger = logging.getLogger(__name__)


def run_prune(
    config_filename,
    repository,
    config,
    hook_context,
    local_borg_version,
    prune_arguments,
    global_arguments,
    dry_run_label,
    local_path,
    remote_path,
):
    '''
    Run the "prune" action for the given repository.
    '''
    if prune_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, prune_arguments.repository
    ):
        return

    borgmatic.hooks.command.execute_hook(
        config.get('before_prune'),
        config.get('umask'),
        config_filename,
        'pre-prune',
        global_arguments.dry_run,
        **hook_context,
    )
    logger.info(f'Pruning archives{dry_run_label}')
    borgmatic.borg.prune.prune_archives(
        global_arguments.dry_run,
        repository['path'],
        config,
        local_borg_version,
        prune_arguments,
        global_arguments,
        local_path=local_path,
        remote_path=remote_path,
    )
    borgmatic.hooks.command.execute_hook(
        config.get('after_prune'),
        config.get('umask'),
        config_filename,
        'post-prune',
        global_arguments.dry_run,
        **hook_context,
    )
