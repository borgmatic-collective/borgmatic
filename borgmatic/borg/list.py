import copy
import logging
import re

from borgmatic.borg import environment
from borgmatic.borg.flags import make_flags, make_flags_from_arguments
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def resolve_archive_name(repository, archive, storage_config, local_path='borg', remote_path=None):
    '''
    Given a local or remote repository path, an archive name, a storage config dict, a local Borg
    path, and a remote Borg path, simply return the archive name. But if the archive name is
    "latest", then instead introspect the repository for the latest archive and return its name.

    Raise ValueError if "latest" is given but there are no archives in the repository.
    '''
    if archive != "latest":
        return archive

    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'list')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + make_flags('remote-path', remote_path)
        + make_flags('lock-wait', lock_wait)
        + make_flags('last', 1)
        + ('--short', repository)
    )

    output = execute_command(
        full_command,
        output_log_level=None,
        borg_local_path=local_path,
        extra_environment=environment.make_environment(storage_config),
    )
    try:
        latest_archive = output.strip().splitlines()[-1]
    except IndexError:
        raise ValueError('No archives found in the repository')

    logger.debug('{}: Latest archive is {}'.format(repository, latest_archive))

    return latest_archive


MAKE_FLAGS_EXCLUDES = ('repository', 'archive', 'successful', 'paths', 'find_paths')


def make_list_command(
    repository, storage_config, list_arguments, local_path='borg', remote_path=None
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
        + make_flags('remote-path', remote_path)
        + make_flags('lock-wait', lock_wait)
        + make_flags_from_arguments(list_arguments, excludes=MAKE_FLAGS_EXCLUDES,)
        + (
            ('::'.join((repository, list_arguments.archive)),)
            if list_arguments.archive
            else (repository,)
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


def list_archives(repository, storage_config, list_arguments, local_path='borg', remote_path=None):
    '''
    Given a local or remote repository path, a storage config dict, the arguments to the list
    action, and local and remote Borg paths, display the output of listing Borg archives in the
    repository or return JSON output. Or, if an archive name is given, list the files in that
    archive. Or, if list_arguments.find_paths are given, list the files by searching across multiple
    archives.
    '''
    borg_environment = environment.make_environment(storage_config)

    # If there are any paths to find (and there's not a single archive already selected), start by
    # getting a list of archives to search.
    if list_arguments.find_paths and not list_arguments.archive:
        repository_arguments = copy.copy(list_arguments)
        repository_arguments.archive = None
        repository_arguments.json = False
        repository_arguments.format = None

        # Ask Borg to list archives. Capture its output for use below.
        archive_lines = tuple(
            execute_command(
                make_list_command(
                    repository, storage_config, repository_arguments, local_path, remote_path
                ),
                output_log_level=None,
                borg_local_path=local_path,
                extra_environment=borg_environment,
            )
            .strip('\n')
            .split('\n')
        )
    else:
        archive_lines = (list_arguments.archive,)

    # For each archive listed by Borg, run list on the contents of that archive.
    for archive_line in archive_lines:
        try:
            archive = archive_line.split()[0]
        except (AttributeError, IndexError):
            archive = None

        if archive:
            logger.warning(archive_line)

        archive_arguments = copy.copy(list_arguments)
        archive_arguments.archive = archive
        main_command = make_list_command(
            repository, storage_config, archive_arguments, local_path, remote_path
        ) + make_find_paths(list_arguments.find_paths)

        output = execute_command(
            main_command,
            output_log_level=None if list_arguments.json else logging.WARNING,
            borg_local_path=local_path,
            extra_environment=borg_environment,
        )

        if list_arguments.json:
            return output
