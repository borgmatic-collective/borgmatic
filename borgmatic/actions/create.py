import logging

import borgmatic.actions.json
import borgmatic.borg.create
import borgmatic.config.paths
import borgmatic.config.validate
import borgmatic.hooks.dispatch
from borgmatic.actions import pattern

logger = logging.getLogger(__name__)


def run_create(
    config_filename,
    repository,
    config,
    config_paths,
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

    if config.get('list_details') and config.get('progress'):
        raise ValueError(
            'With the create action, only one of --list/--files/list_details and --progress/progress can be used.'
        )

    if config.get('list_details') and create_arguments.json:
        raise ValueError(
            'With the create action, only one of --list/--files/list_details and --json can be used.'
        )

    logger.info(f'Creating archive{dry_run_label}')
    working_directory = borgmatic.config.paths.get_working_directory(config)

    with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )
        patterns = pattern.process_patterns(pattern.collect_patterns(config), working_directory)
        active_dumps = borgmatic.hooks.dispatch.call_hooks(
            'dump_data_sources',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            config_paths,
            borgmatic_runtime_directory,
            patterns,
            global_arguments.dry_run,
        )

        # Process the patterns again in case any data source hooks updated them. Without this step,
        # we could end up with duplicate paths that cause Borg to hang when it tries to read from
        # the same named pipe twice.
        patterns = pattern.process_patterns(
            patterns, working_directory, skip_expand_paths=config_paths
        )
        stream_processes = [process for processes in active_dumps.values() for process in processes]

        json_output = borgmatic.borg.create.create_archive(
            global_arguments.dry_run,
            repository['path'],
            config,
            patterns,
            local_borg_version,
            global_arguments,
            borgmatic_runtime_directory,
            local_path=local_path,
            remote_path=remote_path,
            json=create_arguments.json,
            stream_processes=stream_processes,
        )

        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))

        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )
