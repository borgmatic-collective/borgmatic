import argparse
import collections
import enum
import json
import logging

import binaryornot.helpers

import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.repo_list
import borgmatic.borg.version
import borgmatic.execute

logger = logging.getLogger(__name__)


class Path_type(enum.Enum):
    DIRECTORY = 'd'
    LINK = 'l'
    PIPE = 'p'
    FILE = '-'


# A data structure capturing a path stored in a Borg archive.
Archive_path = collections.namedtuple(
    'Archive_path',
    ('path_type', 'file_path', 'link_target', 'size'),
    defaults=(0,),
)


def get_repository_archives(config, repository):
    '''
    Given a configuration dict and a repository dict, return a list of the repository's archives,
    one dict per archive.
    '''
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        logger.info('Listing repository')
        repo_list_arguments = argparse.Namespace(
            repository=repository['path'],
            short=None,
            format=None,
            json=True,
            prefix=None,
            match_archives=None,
            sort_by=None,
            first=None,
            last=None,
        )
        global_arguments = argparse.Namespace()
        local_path = config.get('local_path', 'borg')
        remote_path = config.get('remote_path')
        local_borg_version = borgmatic.borg.version.local_borg_version(config, local_path)

        return json.loads(
            borgmatic.borg.repo_list.list_repository(
                repository['path'],
                config,
                local_borg_version,
                repo_list_arguments,
                global_arguments,
                local_path,
                remote_path,
            )
        )


def get_archive_paths(config, repository, archive_name):
    '''
    Given a configuration dict, a repository dict, and an archive name in that repository, get a
    generator of files, directories, symlinks, etc. found in the archive, each as an Archive_path
    instance.
    '''
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        logger.info(f'Listing archive {archive_name}')

        global_arguments = argparse.Namespace()
        local_path = config.get('local_path', 'borg')
        remote_path = config.get('remote_path')
        local_borg_version = borgmatic.borg.version.local_borg_version(config, local_path)

        return (
            Archive_path(
                path_data['type'],
                path_data['path'],
                path_data.get('linktarget'),
                path_data.get('size', 0),
            )
            for path_data in borgmatic.borg.list.capture_archive_listing(
                repository['path'],
                archive_name,
                config,
                local_borg_version,
                global_arguments,
                # Explicitly include the size key even if a custom file_list_format is
                # configured, since sizes are always shown in the browse UI.
                path_format='{size}',
                local_path=local_path,
                remote_path=remote_path,
            )
        )


MAXIMUM_TOTAL_READ_SIZE = 100000
TRUNCATION_MESSAGE = '[... truncated for display ...]'


def get_archive_file_content(config, repository, archive_name, file_path):
    '''
    Given a configuration dict, a repository dict, an archive name in that repository, and a file
    path in that archive, return the file's contents or None if the file can't be loaded, e.g.
    because it's binary or can't be decoded.

    If the file is too large, then truncate the returned content.
    '''
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        logger.info(f'Getting archive content of file {file_path}')
        local_path = config.get('local_path', 'borg')
        remote_path = config.get('remote_path')

        extract_process = borgmatic.borg.extract.extract_archive(
            dry_run=False,
            repository=repository['path'],
            archive=archive_name,
            paths=(file_path,),
            config=config,
            local_borg_version=borgmatic.borg.version.local_borg_version(config, local_path),
            global_arguments=argparse.Namespace(),
            local_path=local_path,
            remote_path=remote_path,
            destination_path=None,
            strip_components=None,
            extract_to_stdout=True,
        )

        chunks = []
        read_bytes_count = 0
        terminated = False

        # Capture stdout while logging stderr.
        with borgmatic.logger.Log_prefix(None):  # Log command output without any prefix.
            for chunk in borgmatic.execute.log_outputs(
                processes=(extract_process,),
                exclude_stdouts=(),
                output_log_level=None,
                borg_local_path=local_path,
                borg_exit_codes=config.get('borg_exit_codes'),
                output_raw_bytes=True,
            ):
                read_bytes_count += len(chunk)
                chunks.append(chunk)

                # If we've read our fill of bytes, kill the extract process so we don't have to
                # drain and read the entire file from it.
                if not terminated and read_bytes_count >= MAXIMUM_TOTAL_READ_SIZE:
                    logger.debug(
                        "Terminating Borg extract process, since we've read our fill of file preview data"
                    )
                    extract_process.terminate()
                    terminated = True

        content = b''.join(chunks)

        if binaryornot.helpers.is_binary_string(content):
            return None

        try:
            return (
                content.decode()
                if len(content) < MAXIMUM_TOTAL_READ_SIZE
                else f'{content.decode()}\n{TRUNCATION_MESSAGE}'
            )
        except UnicodeDecodeError:
            return None
