import json
import logging
import os
import shlex
import sys
import tarfile
import threading

import borgmatic.borg.export_tar
import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.hooks.data_source.config
import borgmatic.logger
from borgmatic.execute import execute_command, execute_command_with_processes
from borgmatic.hooks.data_source import dump

logger = logging.getLogger(__name__)


def make_dump_path(base_directory):  # pragma: no cover
    '''
    Given a base directory, make the corresponding dump path.
    '''
    return dump.make_data_source_dump_path(base_directory, 'tarballs')


def get_default_port(databases, config):  # pragma: no cover
    return None


def use_streaming(databases, config):
    '''
    Return whether dump streaming is used for this hook. (Spoiler: It isn't.)
    '''
    return False


def write_manifest(dump_directory, members_metadata):
    '''
    TODO
    '''
    with open(f'{dump_directory}_manifest.json', 'w') as metadata_file:
        metadata_file.write(json.dumps(members_metadata))


STREAM_BLOCK_SIZE = 4096


def dump_data_sources(
    tarballs,
    config,
    config_paths,
    borgmatic_runtime_directory,
    patterns,
    dry_run,
):
    '''
    Extract the given tarballs to a temporary directory on disk. The tarballs are supplied as a
    sequence of configuration dicts, as per the configuration schema. Use the given borgmatic
    runtime directory to construct the destination path.

    Return an empty sequence, since there are no ongoing dump processes from this hook. Also append
    the path of the temporary directory to the given patterns list, so the extracted tarballs
    actually get backed up.
    '''
    dry_run_label = ' (dry run; not actually extracting anything)' if dry_run else ''
    processes = []
    dumps_metadata = []

    logger.info(f'Extracting tarballs{dry_run_label}')

    for tarball in tarballs:
        tarball_name = tarball.get('label', tarball['name'])
        tarball_path = tarball['path']
        dumps_metadata.append(
            borgmatic.actions.restore.Dump('tarballs', tarball_name, label=tarball.get('label'))
        )

        if tarball_name == 'all':
            logger.warning('The "all" name has no meaning for tarballs')

        if not os.path.exists(tarball_path):
            raise ValueError(f'Tarball "{tarball_name}" does not exist: {tarball_path}')

        dump_directory = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), tarball_name, label=tarball.get('label')
        )
        os.makedirs(dump_directory, mode=0o700, exist_ok=True)

        logger.debug(
            f'Extracting tarball at {tarball_path} to {dump_directory}{dry_run_label}',
        )

        if not tarfile.is_tarfile(tarball_path):
            raise ValueError(f'Tarball "{tarball_name}" is not actually a tarball: {tarball_path}')

        tar = tarfile.open(tarball_path)
        members_metadata = {}

        # Create a named pipe per member for streaming directory to Borg.
        for member in tar:
            member_extract_path = os.path.join(dump_directory, member.name)
            member_metadata = member.get_info()
            member_metadata['type'] = ord(member_metadata['type'])
            members_metadata[member.name] = member_metadata

            if member.isdir():
                os.makedirs(member_extract_path, mode=0o700, exist_ok=True)
                continue

            dump.create_named_pipe_for_dump(member_extract_path)

        write_manifest(dump_directory, members_metadata)

    if dry_run:
        return ()

    stream_process = execute_command(
        (sys.executable, '-m', 'borgmatic.hooks.data_source.tarballs'),
        run_to_completion=False,
        environment=dict(
            os.environ,
            BORGMATIC_TARBALLS_CONFIG=json.dumps(tarballs),
            BORGMATIC_RUNTIME_DIRECTORY=borgmatic_runtime_directory,
        ),
    )

    dump.write_data_source_dumps_metadata(borgmatic_runtime_directory, 'tarballs', dumps_metadata)
    borgmatic.hooks.data_source.config.inject_pattern(
        patterns,
        borgmatic.borg.pattern.Pattern(
            os.path.join(borgmatic_runtime_directory, 'tarballs'),
            source=borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    )

    return (stream_process,)


def stream_member(tar_file, dump_directory, member, read_lock):
    '''
    TODO
    '''
    extract_path = os.path.join(dump_directory, member.name)
    pipe = open(extract_path, 'wb')

    # Borg can't include symlinks/hardlinks properly because "--read-special" (which is required for
    # the whole pipe scheme to work) dereferences them. So just leave links (and other special
    # files) as empty files and rely on the per-member metadata we include to allow borgmatic to
    # recreate them properly upon restore.
    if not member.isfile():
        pipe.close()
        return

    buffer = tar_file.extractfile(member)

    while True:
        with read_lock:
            block = buffer.read(STREAM_BLOCK_SIZE)

        if not block:
            break

        pipe.write(block)

    pipe.close()


def stream_tarballs():
    '''
    TODO
    '''
    try:
        tarballs = json.loads(os.environ['BORGMATIC_TARBALLS_CONFIG'])
    except KeyError:
        raise ValueError('Expected BORGMATIC_TARBALLS_CONFIG environment variable is missing')

    try:
        borgmatic_runtime_directory = os.environ['BORGMATIC_RUNTIME_DIRECTORY']
    except KeyError:
        raise ValueError('Expected BORGMATIC_RUNTIME_DIRECTORY environment variable is missing')

    threads = []

    for tarball in tarballs:
        tarball_name = tarball.get('label', tarball['name'])
        tarball_path = tarball['path']
        tar_file = tarfile.open(tarball_path)
        dump_directory = dump.make_data_source_dump_filename(
            make_dump_path(borgmatic_runtime_directory), tarball_name, label=tarball.get('label')
        )
        read_lock = threading.Lock()

        for member in tar_file.getmembers():
            if not member.isdir():
                threads.append(
                    threading.Thread(
                        target=stream_member, args=(tar_file, dump_directory, member, read_lock)
                    )
                )

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


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


# TODO: Need to update all other data source hooks accordingly.
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
    TODO
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

    return json.load(extract_process.stdout)


MARKER_PATH_COMPONENTS = ['borgmatic', 'tarballs']
HOSTNAME_AND_DATA_SOURCE_NAME_PATH_COMPONENTS_COUNT = 2


def strip_member_path_prefix(member_path):
    '''
    TODO
    '''
    path_components = member_path.split(os.path.sep)

    # TODO: Handle the case of no match here.
    for index in range(len(path_components) - len(MARKER_PATH_COMPONENTS)):
        if path_components[index: index + len(MARKER_PATH_COMPONENTS)] == MARKER_PATH_COMPONENTS:
            return os.path.sep.join(path_components[index + len(MARKER_PATH_COMPONENTS) + HOSTNAME_AND_DATA_SOURCE_NAME_PATH_COMPONENTS_COUNT:])

    return None


EXTENSION_TO_TARFILE_COMPRESSION = {
    'gz': 'gz',
    'tgz': 'gz',
    'bz2': 'bz2',
    'tbz': 'bz2',
    'xz': 'xz',
    'txz': 'xz',
    'zstd': 'zst',
    'zst': 'zst',
    'tzst': 'zst',
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
    # TODO: What to do if the path already exists? See what SQLite hook does?
    destination_path = data_source.get('restore_path', data_source['path'])
    # TODO: Handle unknown extension / lz4.
    compression = EXTENSION_TO_TARFILE_COMPRESSION[destination_path.split('.')[-1]]

    # TODO: Somehow handle the dry run case.
    # Stream the "export-tar" from the Borg archive, rewrite it on-the-fly to add missing manifest
    # metadata, and write it out to a destination tarball on disk.
    with tarfile.open(mode='r|', fileobj=extract_process.stdout) as source_tar, tarfile.open(destination_path, mode=f'x:{compression}') as destination_tar:
        for member in source_tar:
            member.name = strip_member_path_prefix(member.name)
            manifest_entry = manifest.get(member.name)

            # You can end up with a member that's in the Borg archive but not the manifest when, for
            # instance, everything in the source tarball is in a subdirectory rather than in the
            # root. For such missing members, simply skip them, as they weren't in the source
            # tarball to begin with.
            if manifest_entry is None:
                continue

            # Set each key/value from the manifest into the tarball member. This is the magic that
            # takes an exported tarball from a Borg archive and rewrites it to correct all the
            # modification times, file modes, ownerships, etc. It also puts back symlinks,
            # hardlinks, special files, etc. that aren't represented properly in the Borg archive
            # due to limitations during the "create".
            for key, value in manifest_entry.items():
                setattr(member, key, bytes([value]) if key == 'type' else value)

            destination_tar.addfile(member, source_tar.extractfile(member) if member.isfile() else None)


if __name__ == '__main__':  # pragma: no cover
    borgmatic.logger.configure_logging(logging.INFO, color_enabled=False)
    stream_tarballs()
