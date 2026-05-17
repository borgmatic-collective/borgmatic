import os
import argparse
import json
import logging

import borgmatic.borg.repo_list
import borgmatic.borg.version


logger = logging.getLogger(__name__)


def get_repository_archives(config, repository):
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        logger.answer('Listing repository')
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


def get_archive_files(config, repository, archive_name):
    with borgmatic.logger.Log_prefix(repository.get('label', repository['path'])):
        logger.answer(f"Listing archive {archive_name}")

        global_arguments = argparse.Namespace()
        local_path = config.get('local_path', 'borg')
        remote_path = config.get('remote_path')
        local_borg_version = borgmatic.borg.version.local_borg_version(config, local_path)

        return sorted(
            dict.fromkeys(
                base_path
                for archive in borgmatic.borg.list.capture_archive_listing(
                    repository['path'],
                    archive_name,
                    config,
                    local_borg_version,
                    global_arguments,
                    list_paths=(r're:^([^/]+/){1,2}[^/]+$',),  # TODO
                    local_path=local_path,
                    remote_path=remote_path,
                )
                for base_path in (archive['path'].split(os.path.sep)[0],)
            ),
        )
