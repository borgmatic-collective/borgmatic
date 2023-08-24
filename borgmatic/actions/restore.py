import copy
import logging
import os

import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.mount
import borgmatic.borg.rlist
import borgmatic.borg.state
import borgmatic.config.validate
import borgmatic.hooks.dispatch
import borgmatic.hooks.dump

logger = logging.getLogger(__name__)


UNSPECIFIED_HOOK = object()


def get_configured_data_source(
    config,
    archive_data_source_names,
    hook_name,
    data_source_name,
    configuration_data_source_name=None,
):
    '''
    Find the first data source with the given hook name and data source name in the configuration
    dict and the given archive data source names dict (from hook name to data source names contained
    in a particular backup archive). If UNSPECIFIED_HOOK is given as the hook name, search all data
    source hooks for the named data source. If a configuration data source name is given, use that
    instead of the data source name to lookup the data source in the given hooks configuration.

    Return the found data source as a tuple of (found hook name, data source configuration dict) or
    (None, None) if not found.
    '''
    if not configuration_data_source_name:
        configuration_data_source_name = data_source_name

    if hook_name == UNSPECIFIED_HOOK:
        hooks_to_search = {
            hook_name: value
            for (hook_name, value) in config.items()
            if hook_name in borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES
        }
    else:
        try:
            hooks_to_search = {hook_name: config[hook_name]}
        except KeyError:
            return (None, None)

    return next(
        (
            (name, hook_data_source)
            for (name, hook) in hooks_to_search.items()
            for hook_data_source in hook
            if hook_data_source['name'] == configuration_data_source_name
            and data_source_name in archive_data_source_names.get(name, [])
        ),
        (None, None),
    )


def restore_single_data_source(
    repository,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    archive_name,
    hook_name,
    data_source,
    connection_params,
):  # pragma: no cover
    '''
    Given (among other things) an archive name, a data source hook name, the hostname, port,
    username/password as connection params, and a configured data source configuration dict, restore
    that data source from the archive.
    '''
    logger.info(
        f'{repository.get("label", repository["path"])}: Restoring data source {data_source["name"]}'
    )

    dump_pattern = borgmatic.hooks.dispatch.call_hooks(
        'make_data_source_dump_pattern',
        config,
        repository['path'],
        borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES,
        data_source['name'],
    )[hook_name]

    # Kick off a single data source extract to stdout.
    extract_process = borgmatic.borg.extract.extract_archive(
        dry_run=global_arguments.dry_run,
        repository=repository['path'],
        archive=archive_name,
        paths=borgmatic.hooks.dump.convert_glob_patterns_to_borg_patterns([dump_pattern]),
        config=config,
        local_borg_version=local_borg_version,
        global_arguments=global_arguments,
        local_path=local_path,
        remote_path=remote_path,
        destination_path='/',
        # A directory format dump isn't a single file, and therefore can't extract
        # to stdout. In this case, the extract_process return value is None.
        extract_to_stdout=bool(data_source.get('format') != 'directory'),
    )

    # Run a single data source restore, consuming the extract stdout (if any).
    borgmatic.hooks.dispatch.call_hooks(
        function_name='restore_data_source_dump',
        config=config,
        log_prefix=repository['path'],
        hook_names=[hook_name],
        data_source=data_source,
        dry_run=global_arguments.dry_run,
        extract_process=extract_process,
        connection_params=connection_params,
    )


def collect_archive_data_source_names(
    repository,
    archive,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Given a local or remote repository path, a resolved archive name, a configuration dict, the
    local Borg version, global_arguments an argparse.Namespace, and local and remote Borg paths,
    query the archive for the names of data sources it contains as dumps and return them as a dict
    from hook name to a sequence of data source names.
    '''
    borgmatic_source_directory = os.path.expanduser(
        config.get(
            'borgmatic_source_directory', borgmatic.borg.state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY
        )
    ).lstrip('/')
    dump_paths = borgmatic.borg.list.capture_archive_listing(
        repository,
        archive,
        config,
        local_borg_version,
        global_arguments,
        list_paths=[
            os.path.expanduser(
                borgmatic.hooks.dump.make_data_source_dump_path(borgmatic_source_directory, pattern)
            )
            for pattern in ('*_databases/*/*',)
        ],
        local_path=local_path,
        remote_path=remote_path,
    )

    # Determine the data source names corresponding to the dumps found in the archive and
    # add them to restore_names.
    archive_data_source_names = {}

    for dump_path in dump_paths:
        try:
            (hook_name, _, data_source_name) = dump_path.split(
                borgmatic_source_directory + os.path.sep, 1
            )[1].split(os.path.sep)[0:3]
        except (ValueError, IndexError):
            logger.warning(
                f'{repository}: Ignoring invalid data source dump path "{dump_path}" in archive {archive}'
            )
        else:
            if data_source_name not in archive_data_source_names.get(hook_name, []):
                archive_data_source_names.setdefault(hook_name, []).extend([data_source_name])

    return archive_data_source_names


def find_data_sources_to_restore(requested_data_source_names, archive_data_source_names):
    '''
    Given a sequence of requested data source names to restore and a dict of hook name to the names
    of data sources found in an archive, return an expanded sequence of data source names to
    restore, replacing "all" with actual data source names as appropriate.

    Raise ValueError if any of the requested data source names cannot be found in the archive.
    '''
    # A map from data source hook name to the data source names to restore for that hook.
    restore_names = (
        {UNSPECIFIED_HOOK: requested_data_source_names}
        if requested_data_source_names
        else {UNSPECIFIED_HOOK: ['all']}
    )

    # If "all" is in restore_names, then replace it with the names of dumps found within the
    # archive.
    if 'all' in restore_names[UNSPECIFIED_HOOK]:
        restore_names[UNSPECIFIED_HOOK].remove('all')

        for hook_name, data_source_names in archive_data_source_names.items():
            restore_names.setdefault(hook_name, []).extend(data_source_names)

            # If a data source is to be restored as part of "all", then remove it from restore names
            # so it doesn't get restored twice.
            for data_source_name in data_source_names:
                if data_source_name in restore_names[UNSPECIFIED_HOOK]:
                    restore_names[UNSPECIFIED_HOOK].remove(data_source_name)

    if not restore_names[UNSPECIFIED_HOOK]:
        restore_names.pop(UNSPECIFIED_HOOK)

    combined_restore_names = set(
        name for data_source_names in restore_names.values() for name in data_source_names
    )
    combined_archive_data_source_names = set(
        name
        for data_source_names in archive_data_source_names.values()
        for name in data_source_names
    )

    missing_names = sorted(set(combined_restore_names) - combined_archive_data_source_names)
    if missing_names:
        joined_names = ', '.join(f'"{name}"' for name in missing_names)
        raise ValueError(
            f"Cannot restore data source{'s' if len(missing_names) > 1 else ''} {joined_names} missing from archive"
        )

    return restore_names


def ensure_data_sources_found(restore_names, remaining_restore_names, found_names):
    '''
    Given a dict from hook name to data source names to restore, a dict from hook name to remaining
    data source names to restore, and a sequence of found (actually restored) data source names,
    raise ValueError if requested data source to restore were missing from the archive and/or
    configuration.
    '''
    combined_restore_names = set(
        name
        for data_source_names in tuple(restore_names.values())
        + tuple(remaining_restore_names.values())
        for name in data_source_names
    )

    if not combined_restore_names and not found_names:
        raise ValueError('No data sources were found to restore')

    missing_names = sorted(set(combined_restore_names) - set(found_names))
    if missing_names:
        joined_names = ', '.join(f'"{name}"' for name in missing_names)
        raise ValueError(
            f"Cannot restore data source{'s' if len(missing_names) > 1 else ''} {joined_names} missing from borgmatic's configuration"
        )


def run_restore(
    repository,
    config,
    local_borg_version,
    restore_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "restore" action for the given repository, but only if the repository matches the
    requested repository in restore arguments.

    Raise ValueError if a configured data source could not be found to restore.
    '''
    if restore_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, restore_arguments.repository
    ):
        return

    logger.info(
        f'{repository.get("label", repository["path"])}: Restoring data sources from archive {restore_arguments.archive}'
    )

    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_data_source_dumps',
        config,
        repository['path'],
        borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES,
        global_arguments.dry_run,
    )

    archive_name = borgmatic.borg.rlist.resolve_archive_name(
        repository['path'],
        restore_arguments.archive,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
    )
    archive_data_source_names = collect_archive_data_source_names(
        repository['path'],
        archive_name,
        config,
        local_borg_version,
        global_arguments,
        local_path,
        remote_path,
    )
    restore_names = find_data_sources_to_restore(
        restore_arguments.data_sources, archive_data_source_names
    )
    found_names = set()
    remaining_restore_names = {}
    connection_params = {
        'hostname': restore_arguments.hostname,
        'port': restore_arguments.port,
        'username': restore_arguments.username,
        'password': restore_arguments.password,
        'restore_path': restore_arguments.restore_path,
    }

    for hook_name, data_source_names in restore_names.items():
        for data_source_name in data_source_names:
            found_hook_name, found_data_source = get_configured_data_source(
                config, archive_data_source_names, hook_name, data_source_name
            )

            if not found_data_source:
                remaining_restore_names.setdefault(found_hook_name or hook_name, []).append(
                    data_source_name
                )
                continue

            found_names.add(data_source_name)
            restore_single_data_source(
                repository,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                archive_name,
                found_hook_name or hook_name,
                dict(found_data_source, **{'schemas': restore_arguments.schemas}),
                connection_params,
            )

    # For any data sources that weren't found via exact matches in the configuration, try to
    # fallback to "all" entries.
    for hook_name, data_source_names in remaining_restore_names.items():
        for data_source_name in data_source_names:
            found_hook_name, found_data_source = get_configured_data_source(
                config, archive_data_source_names, hook_name, data_source_name, 'all'
            )

            if not found_data_source:
                continue

            found_names.add(data_source_name)
            data_source = copy.copy(found_data_source)
            data_source['name'] = data_source_name

            restore_single_data_source(
                repository,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                archive_name,
                found_hook_name or hook_name,
                dict(data_source, **{'schemas': restore_arguments.schemas}),
                connection_params,
            )

    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_data_source_dumps',
        config,
        repository['path'],
        borgmatic.hooks.dump.DATA_SOURCE_HOOK_NAMES,
        global_arguments.dry_run,
    )

    ensure_data_sources_found(restore_names, remaining_restore_names, found_names)
