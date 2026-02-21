import contextlib
import glob
import importlib
import itertools
import json
import logging
import os

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.hooks.data_source.config

logger = logging.getLogger(__name__)


def use_streaming(hook_config, config):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


MAXIMUM_CONFIG_SYMLINKS_TO_FOLLOW = 10


def resolve_config_path_symlinks(path):
    '''
    Given a path, resolve and yield each successive symlink until the final non-symlink target. If
    the given path isn't a symlink, then just yield it.

    Raise ValueError if we have to follow too many symlinks without getting to the final target.
    '''
    original_path = path

    for _ in range(MAXIMUM_CONFIG_SYMLINKS_TO_FOLLOW):
        yield os.path.abspath(path)

        if not os.path.islink(path):
            return

        path = os.readlink(path)

    raise ValueError(f'Too many symlinks to follow for configuration path: {original_path}')


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

    If any configuration paths are symlinks, then store each symlink along with any destination
    paths as well.

    Return an empty sequence, since there are no ongoing dump processes from this hook.
    '''
    if hook_config and hook_config.get('store_config_files') is False:
        return []

    borgmatic_manifest_path = os.path.join(
        borgmatic_runtime_directory,
        'bootstrap',
        'manifest.json',
    )

    resolved_config_paths = tuple(
        itertools.chain.from_iterable(resolve_config_path_symlinks(path) for path in config_paths)
    )

    if dry_run:
        return []

    os.makedirs(os.path.dirname(borgmatic_manifest_path), exist_ok=True)

    with open(borgmatic_manifest_path, 'w', encoding='utf-8') as manifest_file:
        json.dump(
            {
                'borgmatic_version': importlib.metadata.version('borgmatic'),
                'config_paths': resolved_config_paths,
            },
            manifest_file,
        )

    borgmatic.hooks.data_source.config.inject_pattern(
        patterns,
        borgmatic.borg.pattern.Pattern(
            os.path.join(borgmatic_runtime_directory, 'bootstrap'),
            source=borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    )

    for config_path in resolved_config_paths:
        borgmatic.hooks.data_source.config.inject_pattern(
            patterns,
            borgmatic.borg.pattern.Pattern(
                config_path,
                source=borgmatic.borg.pattern.Pattern_source.HOOK,
            ),
        )

    return []


def remove_data_source_dumps(hook_config, config, borgmatic_runtime_directory, patterns, dry_run):
    '''
    Given a bootstrap configuration dict, a configuration dict, the borgmatic runtime directory, the
    configured patterns, and whether this is a dry run, then remove the manifest file created above.
    If this is a dry run, then don't actually remove anything.
    '''
    dry_run_label = ' (dry run; not actually removing anything)' if dry_run else ''

    manifest_glob = os.path.join(
        borgmatic.config.paths.replace_temporary_subdirectory_with_glob(
            os.path.normpath(borgmatic_runtime_directory),
        ),
        'bootstrap',
    )
    logger.debug(
        f'Looking for bootstrap manifest files to remove in {manifest_glob}{dry_run_label}',
    )

    for manifest_directory in glob.glob(manifest_glob):
        manifest_file_path = os.path.join(manifest_directory, 'manifest.json')
        logger.debug(f'Removing bootstrap manifest at {manifest_file_path}{dry_run_label}')

        if dry_run:
            continue

        with contextlib.suppress(FileNotFoundError):
            os.remove(manifest_file_path)

        with contextlib.suppress(FileNotFoundError):
            os.rmdir(manifest_directory)


def make_data_source_dump_patterns(
    hook_config,
    config,
    borgmatic_runtime_directory,
    name=None,
    hostname=None,
    port=None,
    container=None,
    label=None,
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
