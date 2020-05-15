import logging

from borgmatic.borg.flags import make_flags, make_flags_from_arguments
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


# A hack to convince Borg to exclude archives ending in ".checkpoint". This assumes that a
# non-checkpoint archive name ends in a digit (e.g. from a timestamp).
BORG_EXCLUDE_CHECKPOINTS_GLOB = '*[0123456789]'


def resolve_archive_name(repository, archive, storage_config, local_path='borg', remote_path=None):
    '''
    Given a local or remote repository path, an archive name, a storage config dict, a local Borg
    path, and a remote Borg path, simply return the archive name. But if the archive name is
    "latest", then instead introspect the repository for the latest successful (non-checkpoint)
    archive, and return its name.

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
        + make_flags('glob-archives', BORG_EXCLUDE_CHECKPOINTS_GLOB)
        + make_flags('last', 1)
        + ('--short', repository)
    )

    output = execute_command(full_command, output_log_level=None, borg_local_path=local_path)
    try:
        latest_archive = output.strip().splitlines()[-1]
    except IndexError:
        raise ValueError('No archives found in the repository')

    logger.debug('{}: Latest archive is {}'.format(repository, latest_archive))

    return latest_archive


def list_archives(repository, storage_config, list_arguments, local_path='borg', remote_path=None):
    '''
    Given a local or remote repository path, a storage config dict, and the arguments to the list
    action, display the output of listing Borg archives in the repository or return JSON output. Or,
    if an archive name is given, listing the files in that archive.
    '''
    lock_wait = storage_config.get('lock_wait', None)
    if list_arguments.successful:
        list_arguments.glob_archives = BORG_EXCLUDE_CHECKPOINTS_GLOB

    full_command = (
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
        + make_flags_from_arguments(
            list_arguments, excludes=('repository', 'archive', 'paths', 'successful')
        )
        + (
            '::'.join((repository, list_arguments.archive))
            if list_arguments.archive
            else repository,
        )
        + (tuple(list_arguments.paths) if list_arguments.paths else ())
    )

    return execute_command(
        full_command,
        output_log_level=None if list_arguments.json else logging.WARNING,
        borg_local_path=local_path,
    )
