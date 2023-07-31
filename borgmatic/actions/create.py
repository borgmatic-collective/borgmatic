import json
import logging
import os

try:
    import importlib_metadata
except ModuleNotFoundError:  # pragma: nocover
    import importlib.metadata as importlib_metadata

import borgmatic.borg.create
import borgmatic.borg.state
import borgmatic.config.validate
import borgmatic.hooks.command
import borgmatic.hooks.dispatch
import borgmatic.hooks.dump

logger = logging.getLogger(__name__)


def create_borgmatic_manifest(config, config_paths, dry_run):
    '''
    Create a borgmatic manifest file to store the paths to the configuration files used to create
    the archive.
    '''
    if dry_run:
        return

    borgmatic_source_directory = config.get(
        'borgmatic_source_directory', borgmatic.borg.state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY
    )

    borgmatic_manifest_path = os.path.expanduser(
        os.path.join(borgmatic_source_directory, 'bootstrap', 'manifest.json')
    )

    if not os.path.exists(borgmatic_manifest_path):
        os.makedirs(os.path.dirname(borgmatic_manifest_path), exist_ok=True)

    with open(borgmatic_manifest_path, 'w') as config_list_file:
        json.dump(
            {
                'borgmatic_version': importlib_metadata.version('borgmatic'),
                'config_paths': config_paths,
            },
            config_list_file,
        )


def run_create(
    config_filename,
    repository,
    config,
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
    if create_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, create_arguments.repository
    ):
        return

    borgmatic.hooks.command.execute_hook(
        config.get('before_backup'),
        config.get('umask'),
        config_filename,
        'pre-backup',
        global_arguments.dry_run,
        **hook_context,
    )
    logger.info(f'{repository.get("label", repository["path"])}: Creating archive{dry_run_label}')
    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_database_dumps',
        config,
        repository['path'],
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        global_arguments.dry_run,
    )
    active_dumps = borgmatic.hooks.dispatch.call_hooks(
        'dump_databases',
        config,
        repository['path'],
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        global_arguments.dry_run,
    )
    if config.get('store_config_files', True):
        create_borgmatic_manifest(
            config, global_arguments.used_config_paths, global_arguments.dry_run
        )
    stream_processes = [process for processes in active_dumps.values() for process in processes]

    json_output = borgmatic.borg.create.create_archive(
        global_arguments.dry_run,
        repository['path'],
        config,
        local_borg_version,
        global_arguments,
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
        config,
        config_filename,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        global_arguments.dry_run,
    )
    borgmatic.hooks.command.execute_hook(
        config.get('after_backup'),
        config.get('umask'),
        config_filename,
        'post-backup',
        global_arguments.dry_run,
        **hook_context,
    )
