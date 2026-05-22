import argparse
import json
import logging
import os

import borgmatic.borg.extract
import borgmatic.borg.repo_list
import borgmatic.borg.version

logger = logging.getLogger(__name__)


def get_repository_archives(config, repository):
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


def get_archive_files(config, repository, archive_name, list_path=None):
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        if list_path:
            logger.info(f'Listing archive {archive_name} at path {list_path}')
        else:
            logger.info(f'Listing archive {archive_name}')

        global_arguments = argparse.Namespace()
        local_path = config.get('local_path', 'borg')
        remote_path = config.get('remote_path')
        local_borg_version = borgmatic.borg.version.local_borg_version(config, local_path)
        seen = set()

        return (
            (
                path_data['type']
                if os.path.join(list_path, base_path) == path_data['path']
                else 'd',
                base_path,
                path_data.get('linktarget'),
            )
            for path_data in borgmatic.borg.list.capture_archive_listing(
                repository['path'],
                archive_name,
                config,
                local_borg_version,
                global_arguments,
                list_paths=(rf're:^{list_path}/[^/]+',) if list_path else (r're:^[^/]+',),
                local_path=local_path,
                remote_path=remote_path,
            )
            for base_path in (os.path.relpath(path_data['path'], list_path).split(os.path.sep)[0],)
            if base_path not in seen and not seen.add(base_path)
        )


READLINES_HINT_BYTES = 2000


def get_archive_file_content(config, repository, archive_name, file_path):
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        logger.info(f'Getting archive content of file {file_path}')
        local_path = config.get('local_path', 'borg')
        remote_path = config.get('remote_path')

        lines = borgmatic.borg.extract.extract_archive(
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
        ).stdout.readlines(READLINES_HINT_BYTES)

        content = ''.join(line.decode() for line in lines)

        return content if len(content) < READLINES_HINT_BYTES else f'{content}[...]'
