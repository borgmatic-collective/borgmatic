import collections
import logging
import os
import pathlib
import shutil
import tempfile

import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.mount
import borgmatic.borg.repo_list
import borgmatic.config.paths
import borgmatic.config.validate
import borgmatic.hooks.data_source.dump
import borgmatic.hooks.dispatch

logger = logging.getLogger(__name__)


UNSPECIFIED = object()


Dump = collections.namedtuple(
    'Dump',
    ('hook_name', 'data_source_name', 'hostname', 'port'),
    defaults=('localhost', None),
)


def dumps_match(first, second, default_port=None):
    '''
    Compare two Dump instances for equality while supporting a field value of UNSPECIFIED, which
    indicates that the field should match any value. If a default port is given, then consider any
    dump having that port to match with a dump having a None port.
    '''
    for field_name in first._fields:
        first_value = getattr(first, field_name)
        second_value = getattr(second, field_name)

        if default_port is not None and field_name == 'port':
            if first_value == default_port and second_value is None:
                continue
            if second_value == default_port and first_value is None:
                continue

        if first_value == UNSPECIFIED or second_value == UNSPECIFIED:
            continue

        if first_value != second_value:
            return False

    return True


def render_dump_metadata(dump):
    '''
    Given a Dump instance, make a display string describing it for use in log messages.
    '''
    name = 'unspecified' if dump.data_source_name is UNSPECIFIED else dump.data_source_name
    hostname = dump.hostname or UNSPECIFIED
    port = None if dump.port is UNSPECIFIED else dump.port

    if port:
        metadata = f'{name}@:{port}' if hostname is UNSPECIFIED else f'{name}@{hostname}:{port}'
    else:
        metadata = f'{name}' if hostname is UNSPECIFIED else f'{name}@{hostname}'

    if dump.hook_name not in (None, UNSPECIFIED):
        return f'{metadata} ({dump.hook_name})'

    return metadata


def get_configured_data_source(config, restore_dump):
    '''
    Search in the given configuration dict for dumps corresponding to the given dump to restore. If
    there are multiple matches, error.

    Return the found data source as a data source configuration dict or None if not found.
    '''
    try:
        hooks_to_search = {restore_dump.hook_name: config[restore_dump.hook_name]}
    except KeyError:
        return None

    matching_dumps = tuple(
        hook_data_source
        for (hook_name, hook_config) in hooks_to_search.items()
        for hook_data_source in hook_config
        for default_port in (
            borgmatic.hooks.dispatch.call_hook(
                function_name='get_default_port',
                config=config,
                hook_name=hook_name,
            ),
        )
        if dumps_match(
            Dump(
                hook_name,
                hook_data_source.get('name'),
                hook_data_source.get('hostname', 'localhost'),
                hook_data_source.get('port'),
            ),
            restore_dump,
            default_port,
        )
    )

    if not matching_dumps:
        return None

    if len(matching_dumps) > 1:
        raise ValueError(
            f'Cannot restore data source {render_dump_metadata(restore_dump)} because there are multiple matching data sources configured'
        )

    return matching_dumps[0]


def strip_path_prefix_from_extracted_dump_destination(
    destination_path, borgmatic_runtime_directory
):
    '''
    Directory-format dump files get extracted into a temporary directory containing a path prefix
    that depends how the files were stored in the archive. So, given the destination path where the
    dump was extracted and the borgmatic runtime directory, move the dump files such that the
    restore doesn't have to deal with that varying path prefix.

    For instance, if the dump was extracted to:

      /run/user/0/borgmatic/tmp1234/borgmatic/postgresql_databases/test/...

    or:

      /run/user/0/borgmatic/tmp1234/root/.borgmatic/postgresql_databases/test/...

    then this function moves it to:

      /run/user/0/borgmatic/postgresql_databases/test/...
    '''
    for subdirectory_path, _, _ in os.walk(destination_path):
        databases_directory = os.path.basename(subdirectory_path)

        if not databases_directory.endswith('_databases'):
            continue

        shutil.move(
            subdirectory_path, os.path.join(borgmatic_runtime_directory, databases_directory)
        )
        break


def restore_single_dump(
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
    borgmatic_runtime_directory,
):
    '''
    Given (among other things) an archive name, a data source hook name, the hostname, port,
    username/password as connection params, and a configured data source configuration dict, restore
    that data source from the archive.
    '''
    dump_metadata = render_dump_metadata(
        Dump(hook_name, data_source['name'], data_source.get('hostname'), data_source.get('port'))
    )

    logger.info(f'Restoring data source {dump_metadata}')

    dump_patterns = borgmatic.hooks.dispatch.call_hooks(
        'make_data_source_dump_patterns',
        config,
        borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
        borgmatic_runtime_directory,
        data_source['name'],
    )[hook_name.split('_databases', 1)[0]]

    destination_path = (
        tempfile.mkdtemp(dir=borgmatic_runtime_directory)
        if data_source.get('format') == 'directory'
        else None
    )

    try:
        # Kick off a single data source extract. If using a directory format, extract to a temporary
        # directory. Otherwise extract the single dump file to stdout.
        extract_process = borgmatic.borg.extract.extract_archive(
            dry_run=global_arguments.dry_run,
            repository=repository['path'],
            archive=archive_name,
            paths=[
                borgmatic.hooks.data_source.dump.convert_glob_patterns_to_borg_pattern(
                    dump_patterns
                )
            ],
            config=config,
            local_borg_version=local_borg_version,
            global_arguments=global_arguments,
            local_path=local_path,
            remote_path=remote_path,
            destination_path=destination_path,
            # A directory format dump isn't a single file, and therefore can't extract
            # to stdout. In this case, the extract_process return value is None.
            extract_to_stdout=bool(data_source.get('format') != 'directory'),
        )

        if destination_path and not global_arguments.dry_run:
            strip_path_prefix_from_extracted_dump_destination(
                destination_path, borgmatic_runtime_directory
            )
    finally:
        if destination_path and not global_arguments.dry_run:
            shutil.rmtree(destination_path, ignore_errors=True)

    # Run a single data source restore, consuming the extract stdout (if any).
    borgmatic.hooks.dispatch.call_hook(
        function_name='restore_data_source_dump',
        config=config,
        hook_name=hook_name,
        data_source=data_source,
        dry_run=global_arguments.dry_run,
        extract_process=extract_process,
        connection_params=connection_params,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    )


def collect_dumps_from_archive(
    repository,
    archive,
    config,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    borgmatic_runtime_directory,
):
    '''
    Given a local or remote repository path, a resolved archive name, a configuration dict, the
    local Borg version, global arguments an argparse.Namespace, local and remote Borg paths, and the
    borgmatic runtime directory, query the archive for the names of data sources dumps it contains
    and return them as a set of Dump instances.
    '''
    borgmatic_source_directory = str(
        pathlib.Path(borgmatic.config.paths.get_borgmatic_source_directory(config))
    )

    # Probe for the data source dumps in multiple locations, as the default location has moved to
    # the borgmatic runtime directory (which gets stored as just "/borgmatic" with Borg 1.4+). But
    # we still want to support reading dumps from previously created archives as well.
    dump_paths = borgmatic.borg.list.capture_archive_listing(
        repository,
        archive,
        config,
        local_borg_version,
        global_arguments,
        list_paths=[
            'sh:'
            + borgmatic.hooks.data_source.dump.make_data_source_dump_path(
                base_directory, '*_databases/*/*'
            )
            for base_directory in (
                'borgmatic',
                borgmatic.config.paths.make_runtime_directory_glob(borgmatic_runtime_directory),
                borgmatic_source_directory.lstrip('/'),
            )
        ],
        local_path=local_path,
        remote_path=remote_path,
    )

    # Parse the paths of dumps found in the archive to get their respective dump metadata.
    dumps_from_archive = set()

    for dump_path in dump_paths:
        if not dump_path:
            continue

        # Probe to find the base directory that's at the start of the dump path.
        for base_directory in (
            'borgmatic',
            borgmatic_runtime_directory,
            borgmatic_source_directory,
        ):
            try:
                (hook_name, host_and_port, data_source_name) = dump_path.split(
                    base_directory + os.path.sep, 1
                )[1].split(os.path.sep)[0:3]
            except (ValueError, IndexError):
                continue

            parts = host_and_port.split(':', 1)

            if len(parts) == 1:
                parts += (None,)

            (hostname, port) = parts

            try:
                port = int(port)
            except (ValueError, TypeError):
                port = None

            dumps_from_archive.add(Dump(hook_name, data_source_name, hostname, port))

            # We've successfully parsed the dump path, so need to probe any further.
            break
        else:
            logger.warning(
                f'Ignoring invalid data source dump path "{dump_path}" in archive {archive}'
            )

    return dumps_from_archive


def get_dumps_to_restore(restore_arguments, dumps_from_archive):
    '''
    Given restore arguments as an argparse.Namespace instance indicating which dumps to restore and
    a set of Dump instances representing the dumps found in an archive, return a set of specific
    Dump instances from the archive to restore. As part of this, replace any Dump having a data
    source name of "all" with multiple named Dump instances as appropriate.

    Raise ValueError if any of the requested data source names cannot be found in the archive or if
    there are multiple archive dump matches for a given requested dump.
    '''
    requested_dumps = (
        {
            Dump(
                hook_name=(
                    (
                        restore_arguments.hook
                        if restore_arguments.hook.endswith('_databases')
                        else f'{restore_arguments.hook}_databases'
                    )
                    if restore_arguments.hook
                    else UNSPECIFIED
                ),
                data_source_name=name,
                hostname=restore_arguments.original_hostname or UNSPECIFIED,
                port=restore_arguments.original_port,
            )
            for name in restore_arguments.data_sources or (UNSPECIFIED,)
        }
        if restore_arguments.hook
        or restore_arguments.data_sources
        or restore_arguments.original_hostname
        or restore_arguments.original_port
        else {
            Dump(
                hook_name=UNSPECIFIED,
                data_source_name='all',
                hostname=UNSPECIFIED,
                port=UNSPECIFIED,
            )
        }
    )
    missing_dumps = set()
    dumps_to_restore = set()

    # If there's a requested "all" dump, add every dump from the archive to the dumps to restore.
    if any(dump for dump in requested_dumps if dump.data_source_name == 'all'):
        dumps_to_restore.update(dumps_from_archive)

    # If any archive dump matches a requested dump, add the archive dump to the dumps to restore.
    for requested_dump in requested_dumps:
        if requested_dump.data_source_name == 'all':
            continue

        matching_dumps = tuple(
            archive_dump
            for archive_dump in dumps_from_archive
            if dumps_match(requested_dump, archive_dump)
        )

        if len(matching_dumps) == 0:
            missing_dumps.add(requested_dump)
        elif len(matching_dumps) == 1:
            dumps_to_restore.add(matching_dumps[0])
        else:
            raise ValueError(
                f'Cannot restore data source {render_dump_metadata(requested_dump)} because there are multiple matching dumps in the archive. Try adding flags to disambiguate.'
            )

    if missing_dumps:
        rendered_dumps = ', '.join(
            f'{render_dump_metadata(dump)}' for dump in sorted(missing_dumps)
        )

        raise ValueError(
            f"Cannot restore data source dump{'s' if len(missing_dumps) > 1 else ''} {rendered_dumps} missing from archive"
        )

    return dumps_to_restore


def ensure_requested_dumps_restored(dumps_to_restore, dumps_actually_restored):
    '''
    Given a set of requested dumps to restore and a set of dumps actually restored, raise ValueError
    if any requested dumps to restore weren't restored, indicating that they were missing from the
    configuration.
    '''
    if not dumps_actually_restored:
        raise ValueError('No data source dumps were found to restore')

    missing_dumps = sorted(
        dumps_to_restore - dumps_actually_restored, key=lambda dump: dump.data_source_name
    )

    if missing_dumps:
        rendered_dumps = ', '.join(f'{render_dump_metadata(dump)}' for dump in missing_dumps)

        raise ValueError(
            f"Cannot restore data source{'s' if len(missing_dumps) > 1 else ''} {rendered_dumps} missing from borgmatic's configuration"
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

    Raise ValueError if a configured data source could not be found to restore or there's no
    matching dump in the archive.
    '''
    if restore_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, restore_arguments.repository
    ):
        return

    logger.info(f'Restoring data sources from archive {restore_arguments.archive}')

    with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )

        archive_name = borgmatic.borg.repo_list.resolve_archive_name(
            repository['path'],
            restore_arguments.archive,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        )
        dumps_from_archive = collect_dumps_from_archive(
            repository['path'],
            archive_name,
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
            borgmatic_runtime_directory,
        )
        dumps_to_restore = get_dumps_to_restore(restore_arguments, dumps_from_archive)

        dumps_actually_restored = set()
        connection_params = {
            'hostname': restore_arguments.hostname,
            'port': restore_arguments.port,
            'username': restore_arguments.username,
            'password': restore_arguments.password,
            'restore_path': restore_arguments.restore_path,
        }

        # Restore each dump.
        for restore_dump in dumps_to_restore:
            found_data_source = get_configured_data_source(
                config,
                restore_dump,
            )

            # For a dump that wasn't found via an exact match in the configuration, try to fallback
            # to an "all" data source.
            if not found_data_source:
                found_data_source = get_configured_data_source(
                    config,
                    Dump(restore_dump.hook_name, 'all', restore_dump.hostname, restore_dump.port),
                )

                if not found_data_source:
                    continue

                found_data_source = dict(found_data_source)
                found_data_source['name'] = restore_dump.data_source_name

            dumps_actually_restored.add(restore_dump)

            restore_single_dump(
                repository,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                archive_name,
                restore_dump.hook_name,
                dict(found_data_source, **{'schemas': restore_arguments.schemas}),
                connection_params,
                borgmatic_runtime_directory,
            )

        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )

    ensure_requested_dumps_restored(dumps_to_restore, dumps_actually_restored)
