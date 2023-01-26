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


def get_configured_database(
    hooks, archive_database_names, hook_name, database_name, configuration_database_name=None
):
    '''
    Find the first database with the given hook name and database name in the configured hooks
    dict and the given archive database names dict (from hook name to database names contained in
    a particular backup archive). If UNSPECIFIED_HOOK is given as the hook name, search all database
    hooks for the named database. If a configuration database name is given, use that instead of the
    database name to lookup the database in the given hooks configuration.

    Return the found database as a tuple of (found hook name, database configuration dict).
    '''
    if not configuration_database_name:
        configuration_database_name = database_name

    if hook_name == UNSPECIFIED_HOOK:
        hooks_to_search = hooks
    else:
        hooks_to_search = {hook_name: hooks[hook_name]}

    return next(
        (
            (name, hook_database)
            for (name, hook) in hooks_to_search.items()
            for hook_database in hook
            if hook_database['name'] == configuration_database_name
            and database_name in archive_database_names.get(name, [])
        ),
        (None, None),
    )


def get_configured_hook_name_and_database(hooks, database_name):
    '''
    Find the hook name and first database dict with the given database name in the configured hooks
    dict. This searches across all database hooks.
    '''


def restore_single_database(
    repository,
    location,
    storage,
    hooks,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    archive_name,
    hook_name,
    database,
):  # pragma: no cover
    '''
    Given (among other things) an archive name, a database hook name, and a configured database
    configuration dict, restore that database from the archive.
    '''
    logger.info(f'{repository}: Restoring database {database["name"]}')

    dump_pattern = borgmatic.hooks.dispatch.call_hooks(
        'make_database_dump_pattern',
        hooks,
        repository,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        database['name'],
    )[hook_name]

    # Kick off a single database extract to stdout.
    extract_process = borgmatic.borg.extract.extract_archive(
        dry_run=global_arguments.dry_run,
        repository=repository,
        archive=archive_name,
        paths=borgmatic.hooks.dump.convert_glob_patterns_to_borg_patterns([dump_pattern]),
        location_config=location,
        storage_config=storage,
        local_borg_version=local_borg_version,
        local_path=local_path,
        remote_path=remote_path,
        destination_path='/',
        # A directory format dump isn't a single file, and therefore can't extract
        # to stdout. In this case, the extract_process return value is None.
        extract_to_stdout=bool(database.get('format') != 'directory'),
    )

    # Run a single database restore, consuming the extract stdout (if any).
    borgmatic.hooks.dispatch.call_hooks(
        'restore_database_dump',
        {hook_name: [database]},
        repository,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        global_arguments.dry_run,
        extract_process,
    )


def collect_archive_database_names(
    repository, archive, location, storage, local_borg_version, local_path, remote_path,
):
    '''
    Given a local or remote repository path, a resolved archive name, a location configuration dict,
    a storage configuration dict, the local Borg version, and local and remote Borg paths, query the
    archive for the names of databases it contains and return them as a dict from hook name to a
    sequence of database names.
    '''
    borgmatic_source_directory = os.path.expanduser(
        location.get(
            'borgmatic_source_directory', borgmatic.borg.state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY
        )
    ).lstrip('/')
    parent_dump_path = os.path.expanduser(
        borgmatic.hooks.dump.make_database_dump_path(borgmatic_source_directory, '*_databases/*/*')
    )
    dump_paths = borgmatic.borg.list.capture_archive_listing(
        repository,
        archive,
        storage,
        local_borg_version,
        list_path=parent_dump_path,
        local_path=local_path,
        remote_path=remote_path,
    )

    # Determine the database names corresponding to the dumps found in the archive and
    # add them to restore_names.
    archive_database_names = {}

    for dump_path in dump_paths:
        try:
            (hook_name, _, database_name) = dump_path.split(
                borgmatic_source_directory + os.path.sep, 1
            )[1].split(os.path.sep)[0:3]
        except (ValueError, IndexError):
            logger.warning(
                f'{repository}: Ignoring invalid database dump path "{dump_path}" in archive {archive}'
            )
        else:
            if database_name not in archive_database_names.get(hook_name, []):
                archive_database_names.setdefault(hook_name, []).extend([database_name])

    return archive_database_names


def find_databases_to_restore(requested_database_names, archive_database_names):
    '''
    Given a sequence of requested database names to restore and a dict of hook name to the names of
    databases found in an archive, return an expanded sequence of database names to restore,
    replacing "all" with actual database names as appropriate.

    Raise ValueError if any of the requested database names cannot be found in the archive.
    '''
    # A map from database hook name to the database names to restore for that hook.
    restore_names = (
        {UNSPECIFIED_HOOK: requested_database_names}
        if requested_database_names
        else {UNSPECIFIED_HOOK: ['all']}
    )

    # If "all" is in restore_names, then replace it with the names of dumps found within the
    # archive.
    if 'all' in restore_names[UNSPECIFIED_HOOK]:
        restore_names[UNSPECIFIED_HOOK].remove('all')

        for (hook_name, database_names) in archive_database_names.items():
            restore_names.setdefault(hook_name, []).extend(database_names)

            # If a database is to be restored as part of "all", then remove it from restore names so
            # it doesn't get restored twice.
            for database_name in database_names:
                if database_name in restore_names[UNSPECIFIED_HOOK]:
                    restore_names[UNSPECIFIED_HOOK].remove(database_name)

    if not restore_names[UNSPECIFIED_HOOK]:
        restore_names.pop(UNSPECIFIED_HOOK)

    combined_restore_names = set(
        name for database_names in restore_names.values() for name in database_names
    )
    combined_archive_database_names = set(
        name for database_names in archive_database_names.values() for name in database_names
    )

    missing_names = sorted(set(combined_restore_names) - combined_archive_database_names)
    if missing_names:
        joined_names = ', '.join(f'"{name}"' for name in missing_names)
        raise ValueError(
            f"Cannot restore database{'s' if len(missing_names) > 1 else ''} {joined_names} missing from archive"
        )

    return restore_names


def ensure_databases_found(restore_names, remaining_restore_names, found_names):
    '''
    Given a dict from hook name to database names to restore, a dict from hook name to remaining
    database names to restore, and a sequence of found (actually restored) database names, raise
    ValueError if requested databases to restore were missing from the archive and/or configuration.
    '''
    combined_restore_names = set(
        name
        for database_names in tuple(restore_names.values())
        + tuple(remaining_restore_names.values())
        for name in database_names
    )

    if not combined_restore_names and not found_names:
        raise ValueError('No databases were found to restore')

    missing_names = sorted(set(combined_restore_names) - set(found_names))
    if missing_names:
        joined_names = ', '.join(f'"{name}"' for name in missing_names)
        raise ValueError(
            f"Cannot restore database{'s' if len(missing_names) > 1 else ''} {joined_names} missing from borgmatic's configuration"
        )


def run_restore(
    repository,
    location,
    storage,
    hooks,
    local_borg_version,
    restore_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "restore" action for the given repository, but only if the repository matches the
    requested repository in restore arguments.

    Raise ValueError if a configured database could not be found to restore.
    '''
    if restore_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, restore_arguments.repository
    ):
        return

    logger.info(
        '{}: Restoring databases from archive {}'.format(repository, restore_arguments.archive)
    )
    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_database_dumps',
        hooks,
        repository,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        global_arguments.dry_run,
    )

    archive_name = borgmatic.borg.rlist.resolve_archive_name(
        repository, restore_arguments.archive, storage, local_borg_version, local_path, remote_path,
    )
    archive_database_names = collect_archive_database_names(
        repository, archive_name, location, storage, local_borg_version, local_path, remote_path,
    )
    restore_names = find_databases_to_restore(restore_arguments.databases, archive_database_names)
    found_names = set()
    remaining_restore_names = {}

    for hook_name, database_names in restore_names.items():
        for database_name in database_names:
            found_hook_name, found_database = get_configured_database(
                hooks, archive_database_names, hook_name, database_name
            )

            if not found_database:
                remaining_restore_names.setdefault(found_hook_name or hook_name, []).append(
                    database_name
                )
                continue

            found_names.add(database_name)
            restore_single_database(
                repository,
                location,
                storage,
                hooks,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                archive_name,
                found_hook_name or hook_name,
                found_database,
            )

    # For any database that weren't found via exact matches in the hooks configuration, try to
    # fallback to "all" entries.
    for hook_name, database_names in remaining_restore_names.items():
        for database_name in database_names:
            found_hook_name, found_database = get_configured_database(
                hooks, archive_database_names, hook_name, database_name, 'all'
            )

            if not found_database:
                continue

            found_names.add(database_name)
            database = copy.copy(found_database)
            database['name'] = database_name

            restore_single_database(
                repository,
                location,
                storage,
                hooks,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                archive_name,
                found_hook_name or hook_name,
                database,
            )

    borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
        'remove_database_dumps',
        hooks,
        repository,
        borgmatic.hooks.dump.DATABASE_HOOK_NAMES,
        location,
        global_arguments.dry_run,
    )

    ensure_databases_found(restore_names, remaining_restore_names, found_names)
