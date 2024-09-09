import json
import logging
import os

import borgmatic.borg.extract
import borgmatic.borg.repo_list
import borgmatic.config.validate
import borgmatic.hooks.command
from borgmatic.borg.state import DEFAULT_BORGMATIC_SOURCE_DIRECTORY

logger = logging.getLogger(__name__)


def get_config_paths(bootstrap_arguments, global_arguments, local_borg_version):
    '''
    Given the bootstrap arguments as an argparse.Namespace (containing the repository and archive
    name, borgmatic source directory, destination directory, and whether to strip components), the
    global arguments as an argparse.Namespace (containing the dry run flag and the local borg
    version), return the config paths from the manifest.json file in the borgmatic source directory
    after extracting it from the repository.

    Raise ValueError if the manifest JSON is missing, can't be decoded, or doesn't contain the
    expected configuration path data.
    '''
    borgmatic_source_directory = (
        bootstrap_arguments.borgmatic_source_directory or DEFAULT_BORGMATIC_SOURCE_DIRECTORY
    )
    borgmatic_manifest_path = os.path.expanduser(
        os.path.join(borgmatic_source_directory, 'bootstrap', 'manifest.json')
    )
    config = {'ssh_command': bootstrap_arguments.ssh_command}

    extract_process = borgmatic.borg.extract.extract_archive(
        global_arguments.dry_run,
        bootstrap_arguments.repository,
        borgmatic.borg.repo_list.resolve_archive_name(
            bootstrap_arguments.repository,
            bootstrap_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
        ),
        [borgmatic_manifest_path],
        config,
        local_borg_version,
        global_arguments,
        extract_to_stdout=True,
    )
    manifest_json = extract_process.stdout.read()

    if not manifest_json:
        raise ValueError(
            'Cannot read configuration paths from archive due to missing bootstrap manifest'
        )

    try:
        manifest_data = json.loads(manifest_json)
    except json.JSONDecodeError as error:
        raise ValueError(
            f'Cannot read configuration paths from archive due to invalid bootstrap manifest JSON: {error}'
        )

    try:
        return manifest_data['config_paths']
    except KeyError:
        raise ValueError(
            'Cannot read configuration paths from archive due to invalid bootstrap manifest'
        )


def run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version):
    '''
    Run the "bootstrap" action for the given repository.

    Raise ValueError if the bootstrap configuration could not be loaded.
    Raise CalledProcessError or OSError if Borg could not be run.
    '''
    manifest_config_paths = get_config_paths(
        bootstrap_arguments, global_arguments, local_borg_version
    )
    config = {'ssh_command': bootstrap_arguments.ssh_command}

    logger.info(f"Bootstrapping config paths: {', '.join(manifest_config_paths)}")

    borgmatic.borg.extract.extract_archive(
        global_arguments.dry_run,
        bootstrap_arguments.repository,
        borgmatic.borg.repo_list.resolve_archive_name(
            bootstrap_arguments.repository,
            bootstrap_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
        ),
        [config_path.lstrip(os.path.sep) for config_path in manifest_config_paths],
        config,
        local_borg_version,
        global_arguments,
        extract_to_stdout=False,
        destination_path=bootstrap_arguments.destination,
        strip_components=bootstrap_arguments.strip_components,
        progress=bootstrap_arguments.progress,
    )
