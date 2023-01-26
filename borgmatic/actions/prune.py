import logging

import borgmatic.borg.prune
import borgmatic.hooks.command

logger = logging.getLogger(__name__)


def run_prune(
    config_filename,
    repository,
    storage,
    retention,
    hooks,
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
    borgmatic.hooks.command.execute_hook(
        hooks.get('before_prune'),
        hooks.get('umask'),
        config_filename,
        'pre-prune',
        global_arguments.dry_run,
        **hook_context,
    )
    logger.info('{}: Pruning archives{}'.format(repository, dry_run_label))
    borgmatic.borg.prune.prune_archives(
        global_arguments.dry_run,
        repository,
        storage,
        retention,
        local_borg_version,
        local_path=local_path,
        remote_path=remote_path,
        stats=prune_arguments.stats,
        list_archives=prune_arguments.list_archives,
    )
    borgmatic.hooks.command.execute_hook(
        hooks.get('after_prune'),
        hooks.get('umask'),
        config_filename,
        'post-prune',
        global_arguments.dry_run,
        **hook_context,
    )
