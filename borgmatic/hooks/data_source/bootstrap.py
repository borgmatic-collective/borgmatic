import glob
import importlib
import json
import logging
import os

import borgmatic.borg.pattern
import borgmatic.config.paths

logger = logging.getLogger(__name__)


def use_streaming(hook_config, config):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


def dump_data_sources(
    hook_config,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Given a bootstrap configuration dict, a configuration dict, the borgmatic configuration file
    paths, the borgmatic runtime directory, the configured patterns, and whether this is a dry run,
    create a borgmatic manifest file to store the paths of the configuration files used to create
    the archive. But skip this if the bootstrap store_config_files option is False or if this is a
    dry run.

    Return an empty sequence, since there are no ongoing dump processes from this hook.
    '''
    if hook_config and hook_config.get('store_config_files') is False:
        return []

    borgmatic_manifest_path = os.path.join(
        borgmatic_runtime_directory, 'bootstrap', 'manifest.json'
    )

    if dry_run:
        return []

    os.makedirs(os.path.dirname(borgmatic_manifest_path), exist_ok=True)

    with open(borgmatic_manifest_path, 'w') as manifest_file:
        json.dump(
            {
                'borgmatic_version': importlib.metadata.version('borgmatic'),
                'config_paths': config_paths,
            },
            manifest_file,
        )

    patterns.extend(
        borgmatic.borg.pattern.Pattern(
            config_path, source=borgmatic.borg.pattern.Pattern_source.HOOK
        )
        for config_path in config_paths
    )
    patterns.append(
        borgmatic.borg.pattern.Pattern(
            os.path.join(borgmatic_runtime_directory, 'bootstrap'),
            source=borgmatic.borg.pattern.Pattern_source.HOOK,
        )
    )

    return []


def remove_data_source_dumps(hook_config, config, borgmatic_runtime_directory, dry_run):
    '''
    Given a bootstrap configuration dict, a configuration dict, the borgmatic runtime directory, and
    whether this is a dry run, then remove the manifest file created above. If this is a dry run,
    then don't actually remove anything.
    '''
    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    manifest_glob = os.path.join(
        borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(borgmatic_runtime_directory),
        ),
        'bootstrap',
    )
    logger.debug(
        f'Looking for bootstrap manifest files to remove in {manifest_glob}{dry_run_label}'
    )

    for manifest_directory in glob.glob(manifest_glob):
        manifest_file_path = os.path.join(manifest_directory, 'manifest.json')
        logger.debug(f'Removing bootstrap manifest at {manifest_file_path}{dry_run_label}')

        if dry_run:
            continue

        try:
            os.remove(manifest_file_path)
        except FileNotFoundError:
            pass

        try:
            os.rmdir(manifest_directory)
        except FileNotFoundError:
            pass


def make_data_source_dump_patterns(
    hook_config, config, borgmatic_runtime_directory, name=None
):  # pragma: no cover
    '''
    Restores are implemented via the separate, purpose-specific "bootstrap" action rather than the
    generic "restore".
    '''
    return ()


def restore_data_source_dump(
    hook_config,
    config,
    data_source,
    dry_run,
    extract_process,
    connection_params,
    borgmatic_runtime_directory,
):  # pragma: no cover
    '''
    Restores are implemented via the separate, purpose-specific "bootstrap" action rather than the
    generic "restore".
    '''
    raise NotImplementedError()
