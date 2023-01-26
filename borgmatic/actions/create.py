import json
import logging

import borgmatic.borg.create
import borgmatic.hooks.command
import borgmatic.hooks.dispatch
import borgmatic.hooks.dump

logger = logging.getLogger(__name__)


def run_create(
    config_filename,
    repository,
    location,
    storage,
    hooks,
    hook_context,
    local_borg_version,
    create_arguments,
    global_arguments,
    dry_run_label,
    local_path,
    remote_path,
):
    '''
    Run the "create" action for the given repository.

    If create_arguments.json is True, yield the JSON output from creating the archive.
    '''
    borgmatic.hooks.command.execute_hook(
        hooks.get('before_backup'),
        hooks.get('umask'),
        config_filename,
        'pre-backup',
        global_arguments.dry_run,
        **hook_context,
    )
    logger.info('{}: Creating archive{}'.format(repository, dry_run_label))
    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_database_dumps',
        hooks,
        repository,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        global_arguments.dry_run,
    )
    active_dumps = borgmatic.hooks.dispatch.call_hooks(
        'dump_databases',
        hooks,
        repository,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        global_arguments.dry_run,
    )
    stream_processes = [process for processes in active_dumps.values() for process in processes]

    json_output = borgmatic.borg.create.create_archive(
        global_arguments.dry_run,
        repository,
        location,
        storage,
        local_borg_version,
        local_path=local_path,
        remote_path=remote_path,
        progress=create_arguments.progress,
        stats=create_arguments.stats,
        json=create_arguments.json,
        list_files=create_arguments.list_files,
        stream_processes=stream_processes,
    )
    if json_output:  # pragma: nocover
        yield json.loads(json_output)

    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_database_dumps',
        hooks,
        config_filename,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        global_arguments.dry_run,
    )
    borgmatic.hooks.command.execute_hook(
        hooks.get('after_backup'),
        hooks.get('umask'),
        config_filename,
        'post-backup',
        global_arguments.dry_run,
        **hook_context,
    )
