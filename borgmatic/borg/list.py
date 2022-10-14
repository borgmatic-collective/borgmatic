import argparse
import copy
import logging
import re

from borgmatic.borg import environment, feature, flags, rlist
from borgmatic.execute import execute_command, execute_command_and_capture_output

logger = logging.getLogger(__name__)


ARCHIVE_FILTER_FLAGS_MOVED_TO_RLIST = ('prefix', 'match_archives', 'sort_by', 'first', 'last')
MAKE_FLAGS_EXCLUDES = (
    'repository',
    'archive',
    'successful',
    'paths',
    'find_paths',
) + ARCHIVE_FILTER_FLAGS_MOVED_TO_RLIST


def make_list_command(
    repository,
    storage_config,
    local_borg_version,
    list_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a storage config dict, the arguments to the list
    action, and local and remote Borg paths, return a command as a tuple to list archives or paths
    within an archive.
    '''
    lock_wait = storage_config.get('lock_wait', None)

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
        + flags.make_flags('lock-wait', lock_wait)
        + flags.make_flags_from_arguments(list_arguments, excludes=MAKE_FLAGS_EXCLUDES)
        + (
            flags.make_repository_archive_flags(
                repository, list_arguments.archive, local_borg_version
            )
            if list_arguments.archive
            else flags.make_repository_flags(repository, local_borg_version)
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
        find_path
        if re.compile(r'([-!+RrPp] )|(\w\w:)').match(find_path)
        else f'sh:**/*{find_path}*/**'
        for find_path in find_paths
    )


def list_archive(
    repository,
    storage_config,
    local_borg_version,
    list_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a storage config dict, the local Borg version, the
    arguments to the list action, and local and remote Borg paths, display the output of listing
    the files of a Borg archive (or return JSON output). If list_arguments.find_paths are given,
    list the files by searching across multiple archives. If neither find_paths nor archive name
    are given, instead list the archives in the given repository.
    '''
    if not list_arguments.archive and not list_arguments.find_paths:
        if feature.available(feature.Feature.RLIST, local_borg_version):
            logger.warning(
                'Omitting the --archive flag on the list action is deprecated when using Borg 2.x+. Use the rlist action instead.'
            )

        rlist_arguments = argparse.Namespace(
            repository=repository,
            short=list_arguments.short,
            format=list_arguments.format,
            json=list_arguments.json,
            prefix=list_arguments.prefix,
            match_archives=list_arguments.match_archives,
            sort_by=list_arguments.sort_by,
            first=list_arguments.first,
            last=list_arguments.last,
        )
        return rlist.list_repository(
            repository, storage_config, local_borg_version, rlist_arguments, local_path, remote_path
        )

    if list_arguments.archive:
        for name in ARCHIVE_FILTER_FLAGS_MOVED_TO_RLIST:
            if getattr(list_arguments, name, None):
                logger.warning(
                    f"The --{name.replace('_', '-')} flag on the list action is ignored when using the --archive flag."
                )

    if list_arguments.json:
        raise ValueError(
            'The --json flag on the list action is not supported when using the --archive/--find flags.'
        )

    borg_environment = environment.make_environment(storage_config)

    # If there are any paths to find (and there's not a single archive already selected), start by
    # getting a list of archives to search.
    if list_arguments.find_paths and not list_arguments.archive:
        rlist_arguments = argparse.Namespace(
            repository=repository,
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
                rlist.make_rlist_command(
                    repository,
                    storage_config,
                    local_borg_version,
                    rlist_arguments,
                    local_path,
                    remote_path,
                ),
                extra_environment=borg_environment,
            )
            .strip('\n')
            .split('\n')
        )
    else:
        archive_lines = (list_arguments.archive,)

    # For each archive listed by Borg, run list on the contents of that archive.
    for archive in archive_lines:
        logger.warning(f'{repository}: Listing archive {archive}')

        archive_arguments = copy.copy(list_arguments)
        archive_arguments.archive = archive

        # This list call is to show the files in a single archive, not list multiple archives. So
        # blank out any archive filtering flags. They'll break anyway in Borg 2.
        for name in ARCHIVE_FILTER_FLAGS_MOVED_TO_RLIST:
            setattr(archive_arguments, name, None)

        main_command = make_list_command(
            repository,
            storage_config,
            local_borg_version,
            archive_arguments,
            local_path,
            remote_path,
        ) + make_find_paths(list_arguments.find_paths)

        execute_command(
            main_command,
            output_log_level=logging.WARNING,
            borg_local_path=local_path,
            extra_environment=borg_environment,
        )
