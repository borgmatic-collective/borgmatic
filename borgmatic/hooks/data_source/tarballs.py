import collections
import contextlib
import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile

import borgmatic.borg.export_tar
import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.execute
import borgmatic.hooks.data_source.config
import borgmatic.logger
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'tarballs')


def get_default_port(databases, config):  # pragma: no cover
    return None


def use_streaming(databases, config):  # pragma: no cover
    '''
    Return whether dump streaming is used for this hook.
    '''
    return True


def normalize_member_path(path):
    '''
    Given a member path from a tarball, normalize it, collapsing "." and ".." path components where
    possible.

    Return the normalized result. Raise if the normalized path is still unsafe, e.g. if it's an
    absolute path or starts with ".." even after normalization. Such a path is unsafe because when
    joining the member path together with a parent destination path, it effectively creates an
    "escape" from that parent.
    '''
    normalized = os.path.normpath(path)

    if normalized == '.':
        return normalized

    pieces = normalized.split(os.path.sep)

    if os.path.isabs(normalized) or '..' in pieces:
        raise ValueError(f'Unsafe tarball member path: {path}')

    return normalized


def deduplicate_members(tar_file):
    '''
    Given an open tar file, deduplicate its members and return them as a dict from normalized member
    name to TarInfo instance for that member. The last one with a particular normalized member name
    "wins" and ends up in the resulting dict.

    This is necessary because Borg can't store duplicate paths—and also because we don't want to
    attempt to create duplicate named pipes at the same path.
    '''
    members = {}

    for member in tar_file:
        member_path = normalize_member_path(member.name)

        # Skip storing the root itself.
        if member_path == '.':
            continue

        members[member_path] = member

    return members


def inject_tarball_patterns(
    patterns, members, borgmatic_runtime_directory, dump_directory, manifest_path
):
    '''
    Given a patterns list, a dict from deduplicated tarball member name to corresponding
    tarfile.TarInfo instance, the borgmatic runtime directory, the current dump directory, and the
    tarball manifest path within it, inject all the patterns necessary to backup the tarball into
    the patterns. This includes patterns for:

     * an exclude override for the whole tarballs export directory (to punch through excludes)
     * the tarballs hook dumps JSON file, containing metadata on all the tarball dumps
     * the per-tarball manifest, containing metadata on the members of this tarball
     * every single tarball member path (directories and non-directories separately)

    This spoon-feeding of very specific ordered tarball member paths to Borg is necessary so that it
    reads our named pipes in an expected ordered. That way, we can write to them in the same order
    and service them serially, without the complexity of threads or non-blocking I/O.
    '''
    # Inject an exclude override for the whole tarballs directory, so we don't have to
    # add it per-member and incur the cost of Borg processing all those additional
    # include patterns.
    borgmatic.hooks.data_source.config.inject_pattern(
        patterns,
        borgmatic.borg.pattern.Pattern(
            os.path.join(borgmatic_runtime_directory, 'tarballs'),
            type=borgmatic.borg.pattern.Pattern_type.INCLUDE,
            style=borgmatic.borg.pattern.Pattern_style.PATH_PREFIX,
            source=borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    )

    # Inject a pattern for the hook dumps manifest.
    borgmatic.hooks.data_source.config.inject_pattern(
        patterns,
        borgmatic.borg.pattern.Pattern(
            os.path.join(borgmatic_runtime_directory, 'tarballs', 'dumps.json'),
            source=borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
        override_excludes=False,
    )

    # Inject a pattern for the tarball manifest.
    borgmatic.hooks.data_source.config.inject_pattern(
        patterns,
        borgmatic.borg.pattern.Pattern(
            manifest_path,
            source=borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
        override_excludes=False,
    )

    # Reversed, because successive inject_pattern() calls do inserts, which effectively
    # reverse the order as well. So with the double reverse, they end up back in the
    # expected member order. And do directories first so they end up last. That way,
    # Borg stores the directories but doesn't try to re-read any pipes in those
    # directories.
    for member_path, member in reversed(members.items()):
        if member.isdir():
            borgmatic.hooks.data_source.config.inject_pattern(
                patterns,
                borgmatic.borg.pattern.Pattern(
                    os.path.join(dump_directory, member_path),
                    source=borgmatic.borg.pattern.Pattern_source.HOOK,
                ),
                override_excludes=False,
            )

    for member_path, member in reversed(members.items()):
        if not member.isdir():
            borgmatic.hooks.data_source.config.inject_pattern(
                patterns,
                borgmatic.borg.pattern.Pattern(
                    os.path.join(dump_directory, member_path),
                    source=borgmatic.borg.pattern.Pattern_source.HOOK,
                ),
                override_excludes=False,
            )


def make_member_named_pipes(members, dump_directory, tarball_label, dry_run):
    '''
    Given a dict from deduplicated tarball member name to corresponding tarfile.TarInfo instance,
    the current dump directory, a label for this tarball to use in any error messages, and whether
    this is a dry run, create a named pipe per non-directory member for subsequent streaming
    directly to Borg, mirroring the directory layout from the tarball. But if this is a dry run,
    then don't actually create directories or pipes.

    Return a dict from member path to member metadata dict, suitable for serializing as a tarball
    manifest.

    Raise ValueError if a directory or pipe can't be created due duplicate paths from the tarball.
    '''
    members_metadata = {}

    for member_path, member in members.items():
        member_extract_path = os.path.join(dump_directory, member_path)
        member_metadata = dict(member.get_info())
        member_metadata['name'] = member_path
        member_metadata['type'] = ord(member_metadata['type'])
        members_metadata[member_path] = member_metadata

        if member.isdir():
            if not dry_run:
                try:
                    os.makedirs(member_extract_path, mode=0o700, exist_ok=True)
                except FileExistsError:
                    raise ValueError(
                        f'A file already exists for directory "{member.name}" from tarball "{tarball_label}"'
                    )

            continue

        if not dry_run:
            try:
                dump.create_named_pipe_for_dump(member_extract_path)
            except FileExistsError:
                # This should never happen, because the caller should deduplicate member paths.
                raise ValueError(
                    f'Path "{member.name}" exists multiple times in tarball "{tarball_label}" '
                )

    return members_metadata


def dump_data_sources(
    tarballs,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Given a sequence of tarballs configuration dicts, a top-level configuration dict, a sequence of
    configuration file paths (ignored), the borgmatic runtime directory, a patterns list, and
    whether this is a dry run, stream all the members of the given tarballs to named pipes so that
    Borg can ingest them. Use the given borgmatic runtime directory to construct the destination
    path for the pipes.

    Return a sequence containing the ongoing untarring process. Also append the path of the pipe
    directory to the given patterns list, so the extracted tarballs actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually extracting anything)' if dry_run else ''
    dumps_metadata = []

    logger.info(f'Extracting tarballs{dry_run_label}')
    dump.raise_number_of_files_resource_limit()

    if not tarballs:
        logger.warning('No tarballs are configured to extract')
        return ()

    most_common_name, most_common_count = collections.Counter(
        tarball['name'] for tarball in tarballs
    ).most_common(1)[0]

    if most_common_count > 1:
        raise ValueError(f'Multiple configured tarballs have the same name "{most_common_name}"')

    for tarball in tarballs:
        tarball_label = tarball.get('label', tarball['name'])
        tarball_path = tarball['path']
        dumps_metadata.append(
            borgmatic.actions.restore.Dump('tarballs', tarball['name'], label=tarball.get('label'))
        )

        if tarball['name'] == 'all':  # pragma: no cover
            logger.warning('The "all" name has no meaning for tarballs')

        if not os.path.exists(tarball_path):
            raise ValueError(f'Tarball "{tarball_label}" does not exist: {tarball_path}')

        dump_directory = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), tarball['name'], label=tarball.get('label')
        )
        if not dry_run:
            os.makedirs(dump_directory, mode=0o700, exist_ok=True)

        logger.debug(
            f'Extracting tarball at {tarball_path} to {dump_directory}{dry_run_label}',
        )

        if not tarfile.is_tarfile(tarball_path):
            raise ValueError(f'Tarball "{tarball_label}" is not actually a tarball: {tarball_path}')

        manifest_path = f'{dump_directory}_manifest.json'

        with tarfile.open(tarball_path) as tar_file:
            members = deduplicate_members(tar_file)

            if not dry_run:
                inject_tarball_patterns(
                    patterns, members, borgmatic_runtime_directory, dump_directory, manifest_path
                )

            members_metadata = make_member_named_pipes(
                members, dump_directory, tarball_label, dry_run
            )

        if not dry_run:
            with open(manifest_path, 'w') as manifest_file:
                manifest_file.write(json.dumps(members_metadata))

    if dry_run:
        return ()

    # Start untarring by using Python to invoke this script file itself, which calls
    # stream_tarballs() in a new process. It works this way so that it adheres to the same model as
    # all the database-oriented hooks, which also spin up a new process to stream data directly to
    # Borg.
    stream_process = borgmatic.execute.execute_command(
        (sys.executable, '-m', 'borgmatic.hooks.data_source.tarballs'),
        run_to_completion=False,
        environment=dict(
            os.environ,
            BORGMATIC_TARBALLS_CONFIG=json.dumps(tarballs),
            BORGMATIC_RUNTIME_DIRECTORY=borgmatic_runtime_directory,
        ),
    )

    dump.write_data_source_dumps_metadata(borgmatic_runtime_directory, 'tarballs', dumps_metadata)

    return (stream_process,)


def stream_tarballs(tarballs, borgmatic_runtime_directory):
    '''
    Given a sequence of tarballs configuration dicts and the borgmatic runtime directory, stream
    each member of each tarball through its own named pipe in the runtime directory to Borg. It is
    assumed that these named pipes have already been created and that Borg has been given member
    paths in this precise order (so that Borg will read each pipe as we're writing to it).
    '''
    for tarball in tarballs:
        tarball_path = tarball['path']

        with tarfile.open(tarball_path) as tar_file:
            dump_directory = dump.make_data_source_dump_filename(
                make_dump_path(borgmatic_runtime_directory),
                tarball['name'],
                label=tarball.get('label'),
            )

            for member_path, member in deduplicate_members(tar_file).items():
                if member.isdir():
                    continue

                with open(os.path.join(dump_directory, member_path), 'wb') as pipe:
                    if member.isfile():
                        shutil.copyfileobj(tar_file.extractfile(member), pipe)


def remove_data_source_dumps(
    databases,
    config,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):  # pragma: no cover
    '''
    Remove all database dump files for this hook regardless of the given databases. Use the
    borgmatic runtime directory to construct the destination path. If this is a dry run, then don't
    actually remove anything.
    '''
    dump.remove_data_source_dumps(make_dump_path(borgmatic_runtime_directory), 'tarballs', dry_run)


def make_data_source_dump_patterns(
    databases,
    config,
    borgmatic_runtime_directory,
    name=None,
    hostname=None,
    port=None,
    container=None,
    label=None,
):  # pragma: no cover
    '''
    Given a sequence of configurations dicts, a configuration dict, the borgmatic runtime directory,
    and a database name to match, return the corresponding glob patterns to match the database dump
    in an archive.
    '''
    return (
        dump.make_data_source_dump_filename(
            make_dump_path('borgmatic'), name, hostname, port, container, label
        ),
        dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory),
            name,
            hostname,
            port,
            container,
            label,
        ),
    )


def extract_data_source_dump(
    hook_config,
    config,
    repository,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    archive_name,
    data_source,
    borgmatic_runtime_directory,
):  # pragma: no cover
    '''
    Given a hook configuration dict, a top-level configuration dict, a repository dict, the local
    Borg version, global arguments as an argparse.Namespace instance, the local Borg path, the
    remote Borg path, the archive name to export from, a data source dict, and the borgmatic
    runtime directory, calculate the patterns to look for in the archive and then export a
    corresponding tarball using "export-tar"—streaming via an extract process.

    Return the extract process.
    '''
    return borgmatic.borg.export_tar.export_tar_archive(
        False,
        repository['path'],
        archive_name,
        paths=[
            borgmatic.hooks.data_source.dump.convert_glob_patterns_to_borg_pattern(
                make_data_source_dump_patterns(
                    hook_config,
                    config,
                    borgmatic_runtime_directory,
                    data_source['name'],
                    hostname=None,
                    port=None,
                    container=None,
                    label=data_source.get('label'),
                ),
            ),
        ],
        destination_path='-',  # stdout
        config=config,
        local_borg_version=local_borg_version,
        global_arguments=global_arguments,
        local_path=local_path,
        remote_path=remote_path,
        capture_stdout=True,
    )


def load_data_source_dump_manifest(
    hook_config,
    config,
    repository,
    local_borg_version,
    global_arguments,
    local_path,
    remote_path,
    archive_name,
    data_source,
    borgmatic_runtime_directory,
):
    '''
    Given a hook configuration dict, a top-level configuration dict, a repository dict, the local
    Borg version, global arguments as an argparse.Namespace instance, the local Borg path, the
    remote Borg path, the archive name containing the manifest, a data source dict, and the
    borgmatic runtime directory, extract the manifest for the given data source from the archive,
    parse it as JSON, and return the resulting dict.

    The returned manifest is a map from the path of a file in an archive to the original source
    tarball's TarInfo attributes for this member (as a dict).
    '''
    extract_process = borgmatic.borg.extract.extract_archive(
        dry_run=False,
        repository=repository['path'],
        archive=archive_name,
        paths=[
            borgmatic.hooks.data_source.dump.convert_glob_patterns_to_borg_pattern(
                make_data_source_dump_patterns(
                    hook_config,
                    config,
                    borgmatic_runtime_directory,
                    data_source['name'] + '_manifest.json',
                    data_source.get('hostname'),
                    data_source.get('port'),
                    data_source.get('container'),
                    data_source.get('label'),
                ),
            ),
        ],
        config=config,
        local_borg_version=local_borg_version,
        global_arguments=global_arguments,
        local_path=local_path,
        remote_path=remote_path,
        extract_to_stdout=True,
    )

    # Capture stdout while logging stderr.
    with borgmatic.logger.Log_prefix(None):  # Log command output without any prefix.
        extract_stdout = '\n'.join(
            borgmatic.execute.log_outputs(
                processes=(extract_process,),
                exclude_stdouts=(),
                output_log_level=None,
                borg_local_path=local_path,
                borg_exit_codes=config.get('borg_exit_codes'),
            )
        )

    try:
        return json.loads(extract_stdout)
    except json.JSONDecodeError as error:
        raise ValueError(
            f'Cannot read tarball manifest from archive due to invalid JSON: {error}',
        )


MARKER_PATH_COMPONENTS = ['borgmatic', 'tarballs']
HOSTNAME_AND_DATA_SOURCE_NAME_PATH_COMPONENTS_COUNT = 2


def strip_member_path_prefix(member_path):
    '''
    Given a tar member path, strip off the portion of its path prefix that's stored in the Borg
    archive but isn't in the original tarball. Return the resulting path or None if no prefix is
    found.

    For instance, let's say you've got a tarball containing the member path:

       foo/bar/baz.txt

    ... which might get stored in the Borg archive at the path:

       borgmatic/tarballs/localhost/example/foo/bar/baz.txt

    This function strips off the "borgmatic/tarballs/localhost/example/" portion of that path,
    leaving just the original tarball member path.
    '''
    path_components = member_path.split(os.path.sep)

    for index in range(len(path_components) - len(MARKER_PATH_COMPONENTS)):
        if path_components[index : index + len(MARKER_PATH_COMPONENTS)] == MARKER_PATH_COMPONENTS:
            return normalize_member_path(
                os.path.sep.join(
                    path_components[
                        index
                        + len(MARKER_PATH_COMPONENTS)
                        + HOSTNAME_AND_DATA_SOURCE_NAME_PATH_COMPONENTS_COUNT :
                    ]
                )
            )

    return None


EXTENSION_TO_TARFILE_COMPRESSION = {
    'gz': 'gz',
    'tgz': 'gz',
    'bz2': 'bz2',
    'tbz': 'bz2',
    'tbz2': 'bz2',
    'xz': 'xz',
    'txz': 'xz',
    'tar': '',
}


def restore_data_source_dump(
    hook_config,
    config,
    data_source,
    dry_run,
    extract_process,
    manifest,
    connection_params,
    borgmatic_runtime_directory,
):
    '''
    Given a hook configuration dict (ignored), a configuration dict, a data source dict, whether
    this is a dry run, an extract process as a subprocess.Popen instance, a loaded manifest dict for
    this tarball, connection parameters (ignored), and the borgmatic runtime directory, restore a
    tarball from the given extract stream using the given manifest data. If this is a dry run, then
    don't actually restore anything.
    '''
    destination_path = connection_params.get('restore_path') or data_source.get(
        'restore_path',
        data_source.get('path'),
    )

    dry_run_label = ' (dry run; not actually restoring anything)' if dry_run else ''
    logger.debug(f'Restoring tarball at {destination_path}{dry_run_label}')

    if not dry_run:
        with contextlib.suppress(FileNotFoundError):
            os.remove(destination_path)
            logger.warning(f'Replacing existing tarball at {destination_path}')

    file_extension = destination_path.split('.')[-1]
    try:
        compression = EXTENSION_TO_TARFILE_COMPRESSION[file_extension.lower()]
    except KeyError:
        raise ValueError(f'Unknown tarball compression for {destination_path}')

    # During a dry run, discard any writes to the would-be restored tarball.
    if dry_run:
        write_path = None
        write_buffer = open(os.devnull, 'wb')
    else:
        write_path = destination_path
        write_buffer = None

    # Capture stdout and log stderr.
    with (
        borgmatic.logger.Log_prefix(None),  # Log command output without any prefix.
        borgmatic.execute.Generator_reader(
            borgmatic.execute.log_outputs(
                processes=(extract_process,),
                exclude_stdouts=(),
                output_log_level=None,
                borg_local_path=config.get('local_path', 'borg'),
                borg_exit_codes=config.get('borg_exit_codes'),
                output_raw_bytes=True,
            )
        ) as extract_reader,
    ):
        # Stream the "export-tar" from the Borg archive, rewrite it on-the-fly to add missing manifest
        # metadata, and write it out to a destination tarball on disk.
        try:
            with (
                tarfile.open(mode='r|', fileobj=extract_reader) as exported_tar,
                tarfile.open(
                    write_path, mode=f'x:{compression}', fileobj=write_buffer
                ) as destination_tar,
            ):
                for member in exported_tar:
                    member.name = strip_member_path_prefix(member.name)
                    manifest_entry = manifest.get(member.name)

                    # You can end up with a member that's in the Borg archive but not the manifest when, for
                    # instance, everything in the source tarball is in a subdirectory rather than in the
                    # root—Borg stores parent directories even if they weren't in the source tarball. For
                    # such missing members, simply skip them.
                    if manifest_entry is None:
                        continue

                    # Set each key/value from the manifest into the tarball member. This is the magic that
                    # takes an exported tarball from a Borg archive and rewrites it to correct all the
                    # modification times, file modes, ownerships, etc. It also puts back symlinks,
                    # hardlinks, special files, etc. that aren't represented properly in the Borg archive
                    # due to limitations during the "create".
                    for key, value in manifest_entry.items():
                        setattr(member, key, bytes([value]) if key == 'type' else value)

                    destination_tar.addfile(
                        member, exported_tar.extractfile(member) if member.isfile() else None
                    )
        except (tarfile.ReadError, subprocess.CalledProcessError) as error:
            raise ValueError(f'Error exporting tarball "{destination_path}": {error}')


def main():
    '''
    Given a BORGMATIC_TARBALLS_CONFIG environment variable containing a tarballs configuration dict
    encoded as JSON and a BORGMATIC_RUNTIME_DIRECTORY environment variable containing the borgmatic
    runtime directory, stream each tarball member to Borg.

    This function expects environment variables rather than standard arguments, because it is
    called across a process boundary rather than as a normal function (see dump_data_sources()
    above).
    '''
    borgmatic.logger.configure_logging(logging.INFO, color_enabled=False)

    try:
        tarballs = json.loads(os.environ['BORGMATIC_TARBALLS_CONFIG'])
    except KeyError:
        raise ValueError('Expected BORGMATIC_TARBALLS_CONFIG environment variable is missing')
    except json.JSONDecodeError as error:
        raise ValueError(
            f'Cannot read BORGMATIC_TARBALLS_CONFIG environment variable due to invalid JSON: {error}',
        )

    try:
        borgmatic_runtime_directory = os.environ['BORGMATIC_RUNTIME_DIRECTORY']
    except KeyError:
        raise ValueError('Expected BORGMATIC_RUNTIME_DIRECTORY environment variable is missing')

    try:
        stream_tarballs(tarballs, borgmatic_runtime_directory)
    except (ValueError, BrokenPipeError, OSError, tarfile.ReadError) as error:
        logger.error(f'An error occurred while streaming tarball data: {error}')
        sys.exit(1)


# This is the entry point that data_source_dumps() uses when it spins up a new process to stream
# tarballs to Borg.
if __name__ == '__main__':  # pragma: no cover
    main()
