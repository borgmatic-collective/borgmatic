import json
import logging
import os

import borgmatic.borg.extract
import borgmatic.borg.repo_list
import borgmatic.config.paths
import borgmatic.config.validate
import borgmatic.hooks.command

logger = logging.getLogger(__name__)


def make_bootstrap_config(bootstrap_arguments):
    '''
    Given the bootstrap arguments as an argparse.Namespace, return a corresponding config dict.
    '''
    return {
        'borgmatic_source_directory': bootstrap_arguments.borgmatic_source_directory,
        'local_path': bootstrap_arguments.local_path,
        'remote_path': bootstrap_arguments.remote_path,
        # In case the repo has been moved or is accessed from a different path at the point of
        # bootstrapping.
        'relocated_repo_access_is_ok': True,
        'ssh_command': bootstrap_arguments.ssh_command,
        'user_runtime_directory': bootstrap_arguments.user_runtime_directory,
    }


def load_config_paths_from_archive(
    repository_path,
    archive_name,
    config,
    local_borg_version,
    global_arguments,
    borgmatic_runtime_directory,
):
    '''
    Given a repository path, an archive name, a configuration dict, the local Borg version, the
    global arguments as an argparse.Namespace, and the borgmatic runtime directory, return the
    config paths from the manifest.json file in the borgmatic source directory or runtime directory
    within the repository archive.

    Raise ValueError if the manifest JSON is missing, can't be decoded, or doesn't contain the
    expected configuration path data.
    '''
    # Probe for the manifest file in multiple locations, as the default location has moved to the
    # borgmatic runtime directory (which gets stored as just "/borgmatic" with Borg 1.4+). But we
    # still want to support reading the manifest from previously created archives as well.
    for base_directory in (
        'borgmatic',
        borgmatic.config.paths.make_runtime_directory_glob(borgmatic_runtime_directory),
        borgmatic.config.paths.get_borgmatic_source_directory(config),
    ):
        borgmatic_manifest_path = 'sh:' + os.path.join(
            base_directory,
            'bootstrap',
            'manifest.json',
        )

        extract_process = borgmatic.borg.extract.extract_archive(
            global_arguments.dry_run,
            repository_path,
            archive_name,
            [borgmatic_manifest_path],
            config,
            local_borg_version,
            global_arguments,
            local_path=config.get('local_path', 'borg'),
            remote_path=config.get('remote_path'),
            extract_to_stdout=True,
        )
        manifest_json = extract_process.stdout.read()

        if manifest_json:
            break
    else:
        raise ValueError(
            'Cannot read configuration paths from archive due to missing archive or bootstrap manifest',
        )

    try:
        manifest_data = json.loads(manifest_json)
    except json.JSONDecodeError as error:
        raise ValueError(
            f'Cannot read configuration paths from archive due to invalid bootstrap manifest JSON: {error}',
        )

    try:
        return manifest_data['config_paths']
    except KeyError:
        raise ValueError(
            'Cannot read configuration paths from archive due to invalid bootstrap manifest',
        )


def run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version):
    '''
    Run the "bootstrap" action for the given repository.

    Raise ValueError if the bootstrap configuration could not be loaded.
    Raise CalledProcessError or OSError if Borg could not be run.
    '''
    config = make_bootstrap_config(bootstrap_arguments)
    archive_name = borgmatic.borg.repo_list.resolve_archive_name(
        bootstrap_arguments.repository,
        bootstrap_arguments.archive,
        config,
        local_borg_version,
        global_arguments,
        local_path=bootstrap_arguments.local_path,
        remote_path=bootstrap_arguments.remote_path,
    )

    with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
        manifest_config_paths = load_config_paths_from_archive(
            bootstrap_arguments.repository,
            archive_name,
            config,
            local_borg_version,
            global_arguments,
            borgmatic_runtime_directory,
        )

    logger.info(f"Bootstrapping config paths: {', '.join(manifest_config_paths)}")

    borgmatic.borg.extract.extract_archive(
        global_arguments.dry_run,
        bootstrap_arguments.repository,
        archive_name,
        [config_path.lstrip(os.path.sep) for config_path in manifest_config_paths],
        # Only add progress here and not the extract_archive() call above, because progress
        # conflicts with extract_to_stdout.
        dict(config, progress=bootstrap_arguments.progress or False),
        local_borg_version,
        global_arguments,
        local_path=bootstrap_arguments.local_path,
        remote_path=bootstrap_arguments.remote_path,
        extract_to_stdout=False,
        destination_path=bootstrap_arguments.destination,
        strip_components=bootstrap_arguments.strip_components,
    )
