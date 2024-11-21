import glob
import importlib.metadata
import itertools
import json
import logging
import os
import pathlib

import borgmatic.actions.json
import borgmatic.borg.create
import borgmatic.config.paths
import borgmatic.config.validate
import borgmatic.hooks.command
import borgmatic.hooks.dispatch
import borgmatic.hooks.dump

logger = logging.getLogger(__name__)


def create_borgmatic_manifest(config, config_paths, borgmatic_runtime_directory, dry_run):
    '''
    Given a configuration dict, a sequence of config file paths, the borgmatic runtime directory,
    and whether this is a dry run, create a borgmatic manifest file to store the paths to the
    configuration files used to create the archive.
    '''
    if dry_run:
        return

    borgmatic_manifest_path = os.path.join(
        borgmatic_runtime_directory, 'bootstrap', 'manifest.json'
    )

    if not os.path.exists(borgmatic_manifest_path):
        os.makedirs(os.path.dirname(borgmatic_manifest_path), exist_ok=True)

    with open(borgmatic_manifest_path, 'w') as config_list_file:
        json.dump(
            {
                'borgmatic_version': importlib.metadata.version('borgmatic'),
                'config_paths': config_paths,
            },
            config_list_file,
        )


def expand_directory(directory, working_directory):
    '''
    Given a directory path, expand any tilde (representing a user's home directory) and any globs
    therein. Return a list of one or more resulting paths.
    '''
    expanded_directory = os.path.join(working_directory or '', os.path.expanduser(directory))

    return glob.glob(expanded_directory) or [expanded_directory]


def expand_directories(directories, working_directory=None):
    '''
    Given a sequence of directory paths and an optional working directory, expand tildes and globs
    in each one. Return all the resulting directories as a single flattened tuple.
    '''
    if directories is None:
        return ()

    return tuple(
        itertools.chain.from_iterable(
            expand_directory(directory, working_directory) for directory in directories
        )
    )


def map_directories_to_devices(directories, working_directory=None):
    '''
    Given a sequence of directories and an optional working directory, return a map from directory
    to an identifier for the device on which that directory resides or None if the path doesn't
    exist.

    This is handy for determining whether two different directories are on the same filesystem (have
    the same device identifier).
    '''
    return {
        directory: os.stat(full_directory).st_dev if os.path.exists(full_directory) else None
        for directory in directories
        for full_directory in (os.path.join(working_directory or '', directory),)
    }


def deduplicate_directories(directory_devices, additional_directory_devices):
    '''
    Given a map from directory to the identifier for the device on which that directory resides,
    return the directories as a sorted sequence with all duplicate child directories removed. For
    instance, if paths is ['/foo', '/foo/bar'], return just: ['/foo']

    The one exception to this rule is if two paths are on different filesystems (devices). In that
    case, they won't get de-duplicated in case they both need to be passed to Borg (e.g. the
    location.one_file_system option is true).

    The idea is that if Borg is given a parent directory, then it doesn't also need to be given
    child directories, because it will naturally spider the contents of the parent directory. And
    there are cases where Borg coming across the same file twice will result in duplicate reads and
    even hangs, e.g. when a database hook is using a named pipe for streaming database dumps to
    Borg.

    If any additional directory devices are given, also deduplicate against them, but don't include
    them in the returned directories.
    '''
    deduplicated = set()
    directories = sorted(directory_devices.keys())
    additional_directories = sorted(additional_directory_devices.keys())
    all_devices = {**directory_devices, **additional_directory_devices}

    for directory in directories:
        deduplicated.add(directory)
        parents = pathlib.PurePath(directory).parents

        # If another directory in the given list (or the additional list) is a parent of current
        # directory (even n levels up) and both are on the same filesystem, then the current
        # directory is a duplicate.
        for other_directory in directories + additional_directories:
            for parent in parents:
                if (
                    pathlib.PurePath(other_directory) == parent
                    and all_devices[directory] is not None
                    and all_devices[other_directory] == all_devices[directory]
                ):
                    if directory in deduplicated:
                        deduplicated.remove(directory)
                    break

    return sorted(deduplicated)


def pattern_root_directories(patterns=None):
    '''
    Given a sequence of patterns, parse out and return just the root directories.
    '''
    if not patterns:
        return []

    return [
        pattern.split(ROOT_PATTERN_PREFIX, maxsplit=1)[1]
        for pattern in patterns
        if pattern.startswith(ROOT_PATTERN_PREFIX)
    ]


def process_source_directories(config, config_paths):
    '''
    Given a configuration dict and a sequence of configuration paths, expand and deduplicate the
    source directories from them.
    '''
    working_directory = borgmatic.config.paths.get_working_directory(config)

    return deduplicate_directories(
        map_directories_to_devices(
            expand_directories(
                tuple(config.get('source_directories', ()))
                + tuple(config_paths if config.get('store_config_files', True) else ()),
                working_directory=working_directory,
            )
        ),
        additional_directory_devices=map_directories_to_devices(
            expand_directories(
                pattern_root_directories(config.get('patterns')),
                working_directory=working_directory,
            )
        ),
    )


def run_create(
    config_filename,
    repository,
    config,
    config_paths,
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

    log_prefix = repository.get('label', repository['path'])
    logger.info(f'{log_prefix}: Creating archive{dry_run_label}')

    with borgmatic.config.paths.Runtime_directory(
        config, log_prefix
    ) as borgmatic_runtime_directory:
        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            repository['path'],
            borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )
        source_directories = process_source_directories(config, config_paths)
        active_dumps = borgmatic.hooks.dispatch.call_hooks(
            'dump_data_sources',
            config,
            repository['path'],
            borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES,
            borgmatic_runtime_directory,
            source_directories,
            global_arguments.dry_run,
        )
        stream_processes = [process for processes in active_dumps.values() for process in processes]

        if config.get('store_config_files', True):
            create_borgmatic_manifest(
                config,
                config_paths,
                borgmatic_runtime_directory,
                global_arguments.dry_run,
            )
            source_directories.append(os.path.join(borgmatic_runtime_directory, 'bootstrap'))

        json_output = borgmatic.borg.create.create_archive(
            global_arguments.dry_run,
            repository['path'],
            config,
            config_paths,
            source_directories,
            local_borg_version,
            global_arguments,
            borgmatic_runtime_directory,
            local_path=local_path,
            remote_path=remote_path,
            progress=create_arguments.progress,
            stats=create_arguments.stats,
            json=create_arguments.json,
            list_files=create_arguments.list_files,
            stream_processes=stream_processes,
        )

        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))

        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            config_filename,
            borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES,
            borgmatic_runtime_directory,
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
