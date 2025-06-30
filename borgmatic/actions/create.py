import logging

import borgmatic.actions.json
import borgmatic.borg.create
import borgmatic.borg.rename
import borgmatic.borg.repo_list
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

        # If we have stream processes, we first create an archive with .checkpoint suffix. This is
        # to make sure we only create a real archive if all the streaming processes completed
        # successfully (create_archive will fail if a streaming process fails, but the archive might
        # have already been created at this point).
        use_checkpoint = bool(stream_processes)

        json_output = borgmatic.borg.create.create_archive(
            global_arguments.dry_run,
            repository['path'],
            config,
            patterns,
            local_borg_version,
            global_arguments,
            borgmatic_runtime_directory,
            archive_suffix='.checkpoint' if use_checkpoint else '',
            local_path=local_path,
            remote_path=remote_path,
            json=create_arguments.json,
            comment=create_arguments.comment,
            stream_processes=stream_processes,
        )

        if use_checkpoint:
            rename_checkpoint_archive(
                repository['path'],
                global_arguments,
                config,
                local_borg_version,
                local_path,
                remote_path,
            )

        if json_output:
            output = borgmatic.actions.json.parse_json(json_output, repository.get('label'))
            if use_checkpoint:
                # Patch archive name and ID
                renamed_archive = borgmatic.borg.repo_list.get_latest_archive(
                    repository['path'],
                    config,
                    local_borg_version,
                    global_arguments,
                    local_path,
                    remote_path,
                )

                output['archive']['name'] = renamed_archive['name']
                output['archive']['id'] = renamed_archive['id']

            yield output

        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )


def rename_checkpoint_archive(
    repository_path,
    global_arguments,
    config,
    local_borg_version,
    local_path,
    remote_path,
):
    '''
    Renames the latest archive to not have a '.checkpoint' suffix.

    Raises ValueError if
    - there is not latest archive
    - the latest archive does not have a '.checkpoint' suffix

    Implementation note: We cannot reliably get the just created archive name.
    So we resort to listing the archives and picking the last one.

    A similar comment applies to retrieving the ID of the renamed archive.
    '''
    archive = borgmatic.borg.repo_list.get_latest_archive(
        repository_path,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
        consider_checkpoints=True,
    )

    archive_name = archive['name']

    if not archive_name.endswith('.checkpoint'):
        raise ValueError(f'Latest archive did not have a .checkpoint suffix. Got: {archive_name}')

    new_archive_name = archive_name.removesuffix('.checkpoint')

    logger.info(f'Renaming archive {archive_name} -> {new_archive_name}')

    borgmatic.borg.rename.rename_archive(
        repository_path,
        archive_name,
        new_archive_name,
        global_arguments.dry_run,
        config,
        local_borg_version,
        local_path,
        remote_path,
    )
