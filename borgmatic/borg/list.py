import argparse
import copy
import logging
import re

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, feature, flags, repo_list
from borgmatic.execute import execute_command, execute_command_and_capture_output

logger = logging.getLogger(__name__)


ARCHIVE_FILTER_FLAGS_MOVED_TO_REPO_LIST = ('prefix', 'match_archives', 'sort_by', 'first', 'last')
MAKE_FLAGS_EXCLUDES = (
    'repository',
    'archive',
    'paths',
    'find_paths',
) + ARCHIVE_FILTER_FLAGS_MOVED_TO_REPO_LIST


def make_list_command(
    repository_path,
    config,
    local_borg_version,
    list_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the arguments to the list action,
    and local and remote Borg paths, return a command as a tuple to list archives or paths within an
    archive.
    '''
    return (
        (local_path, 'list')
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not list_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not list_arguments.json
            else ()
        )
        + flags.make_flags('remote-path', remote_path)
        + flags.make_flags('umask', config.get('umask'))
        + flags.make_flags('log-json', config.get('log_json'))
        + flags.make_flags('lock-wait', config.get('lock_wait'))
        + flags.make_flags_from_arguments(list_arguments, excludes=MAKE_FLAGS_EXCLUDES)
        + (
            flags.make_repository_archive_flags(
                repository_path, list_arguments.archive, local_borg_version
            )
            if list_arguments.archive
            else flags.make_repository_flags(repository_path, local_borg_version)
        )
        + (tuple(list_arguments.paths) if list_arguments.paths else ())
    )


def make_find_paths(find_paths):
    '''
    Given a sequence of path fragments or patterns as passed to `--find`, transform all path
    fragments into glob patterns. Pass through existing patterns untouched.

    For example, given find_paths of:

      ['foo.txt', 'pp:root/somedir']

    ... transform that into:

      ['sh:**/*foo.txt*/**', 'pp:root/somedir']
    '''
    if not find_paths:
        return ()

    return tuple(
        (
            find_path
            if re.compile(r'([-!+RrPp] )|(\w\w:)').match(find_path)
            else f'sh:**/*{find_path}*/**'
        )
        for find_path in find_paths
    )


def capture_archive_listing(
    repository_path,
    archive,
    config,
    local_borg_version,
    global_arguments,
    list_paths=None,
    path_format=None,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, an archive name, a configuration
    dict, the local Borg version, global arguments as an argparse.Namespace,
    the archive paths (or Borg patterns) in which to list files, the Borg path
    format to use for the output, and local and remote Borg paths, capture the
    output of listing that archive and return it as a list of file paths.
    '''
    return tuple(
        execute_command_and_capture_output(
            make_list_command(
                repository_path,
                config,
                local_borg_version,
                argparse.Namespace(
                    repository=repository_path,
                    archive=archive,
                    paths=[path for path in list_paths] if list_paths else None,
                    find_paths=None,
                    json=None,
                    format=path_format or '{path}{NUL}',  # noqa: FS003
                ),
                global_arguments,
                local_path,
                remote_path,
            ),
            environment=environment.make_environment(config),
            working_directory=borgmatic.config.paths.get_working_directory(config),
            borg_local_path=local_path,
            borg_exit_codes=config.get('borg_exit_codes'),
        )
        .strip('\0')
        .split('\0')
    )


def list_archive(
    repository_path,
    config,
    local_borg_version,
    list_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, the
    arguments to the list action as an argparse.Namespace, global arguments as an
    argparse.Namespace, and local and remote Borg paths, display the output of listing the files of
    a Borg archive (or return JSON output). If list_arguments.find_paths are given, list the files
    by searching across multiple archives. If neither find_paths nor archive name are given, instead
    list the archives in the given repository.
    '''
    borgmatic.logger.add_custom_log_levels()

    if not list_arguments.archive and not list_arguments.find_paths:
        if feature.available(feature.Feature.REPO_LIST, local_borg_version):
            logger.warning(
                'Omitting the --archive flag on the list action is deprecated when using Borg 2.x+. Use the repo-list action instead.'
            )

        repo_list_arguments = argparse.Namespace(
            repository=repository_path,
            short=list_arguments.short,
            format=list_arguments.format,
            json=list_arguments.json,
            prefix=list_arguments.prefix,
            match_archives=list_arguments.match_archives,
            sort_by=list_arguments.sort_by,
            first=list_arguments.first,
            last=list_arguments.last,
        )
        return repo_list.list_repository(
            repository_path,
            config,
            local_borg_version,
            repo_list_arguments,
            global_arguments,
            local_path,
            remote_path,
        )

    if list_arguments.archive:
        for name in ARCHIVE_FILTER_FLAGS_MOVED_TO_REPO_LIST:
            if getattr(list_arguments, name, None):
                logger.warning(
                    f"The --{name.replace('_', '-')} flag on the list action is ignored when using the --archive flag."
                )

    if list_arguments.json:
        raise ValueError(
            'The --json flag on the list action is not supported when using the --archive/--find flags.'
        )

    borg_exit_codes = config.get('borg_exit_codes')

    # If there are any paths to find (and there's not a single archive already selected), start by
    # getting a list of archives to search.
    if list_arguments.find_paths and not list_arguments.archive:
        repo_list_arguments = argparse.Namespace(
            repository=repository_path,
            short=True,
            format=None,
            json=None,
            prefix=list_arguments.prefix,
            match_archives=list_arguments.match_archives,
            sort_by=list_arguments.sort_by,
            first=list_arguments.first,
            last=list_arguments.last,
        )

        # Ask Borg to list archives. Capture its output for use below.
        archive_lines = tuple(
            execute_command_and_capture_output(
                repo_list.make_repo_list_command(
                    repository_path,
                    config,
                    local_borg_version,
                    repo_list_arguments,
                    global_arguments,
                    local_path,
                    remote_path,
                ),
                environment=environment.make_environment(config),
                working_directory=borgmatic.config.paths.get_working_directory(config),
                borg_local_path=local_path,
                borg_exit_codes=borg_exit_codes,
            )
            .strip('\n')
            .splitlines()
        )
    else:
        archive_lines = (list_arguments.archive,)

    # For each archive listed by Borg, run list on the contents of that archive.
    for archive in archive_lines:
        logger.answer(f'Listing archive {archive}')

        archive_arguments = copy.copy(list_arguments)
        archive_arguments.archive = archive

        # This list call is to show the files in a single archive, not list multiple archives. So
        # blank out any archive filtering flags. They'll break anyway in Borg 2.
        for name in ARCHIVE_FILTER_FLAGS_MOVED_TO_REPO_LIST:
            setattr(archive_arguments, name, None)

        main_command = make_list_command(
            repository_path,
            config,
            local_borg_version,
            archive_arguments,
            global_arguments,
            local_path,
            remote_path,
        ) + make_find_paths(list_arguments.find_paths)

        execute_command(
            main_command,
            output_log_level=logging.ANSWER,
            environment=environment.make_environment(config),
            working_directory=borgmatic.config.paths.get_working_directory(config),
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
