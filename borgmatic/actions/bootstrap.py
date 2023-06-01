import logging
import os
import json

import borgmatic.borg.extract
import borgmatic.borg.rlist
import borgmatic.config.validate
import borgmatic.hooks.command

from borgmatic.borg.state import DEFAULT_BORGMATIC_SOURCE_DIRECTORY

logger = logging.getLogger(__name__)

def get_config_paths(bootstrap_arguments, global_arguments, local_borg_version):
    borgmatic_source_directory = bootstrap_arguments.borgmatic_source_directory or DEFAULT_BORGMATIC_SOURCE_DIRECTORY
    borgmatic_manifest_path = os.path.expanduser(
        os.path.join(borgmatic_source_directory, 'bootstrap', 'configs-list.json')
    )
    extract_process = borgmatic.borg.extract.extract_archive(
        global_arguments.dry_run,
        bootstrap_arguments.repository,
        borgmatic.borg.rlist.resolve_archive_name(
            bootstrap_arguments.repository,
            bootstrap_arguments.archive or 'latest',
            {},
            local_borg_version,
            global_arguments
        ),
        [borgmatic_manifest_path],
        {},
        {},
        local_borg_version,
        global_arguments,
        extract_to_stdout=True,
    )

    try:
        manifest_data = json.loads(extract_process.stdout.read())
    except json.decoder.JSONDecodeError as error:
        logger.error('Error parsing manifest data: %s', error)
        raise

    return manifest_data['config_paths']

    


def run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version):
    '''
    Run the "bootstrap" action for the given repository.
    '''
    manifest_config_paths = get_config_paths(bootstrap_arguments, global_arguments, local_borg_version)

    for config_path in manifest_config_paths:
        logger.info('Bootstrapping config path %s', config_path)

        borgmatic.borg.extract.extract_archive(
            global_arguments.dry_run,
            bootstrap_arguments.repository,
            borgmatic.borg.rlist.resolve_archive_name(
                bootstrap_arguments.repository,
                bootstrap_arguments.archive or 'latest',
                {},
                local_borg_version,
                global_arguments
            ),
            [config_path],
            {},
            {},
            local_borg_version,
            global_arguments,
            extract_to_stdout=False,
            destination_path=bootstrap_arguments.destination or '/',
            strip_components=bootstrap_arguments.strip_components,
            progress=bootstrap_arguments.progress,
        )

        


