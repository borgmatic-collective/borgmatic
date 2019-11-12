import logging
import os

from borgmatic.execute import execute_command, execute_command_without_capture

logger = logging.getLogger(__name__)


def extract_last_archive_dry_run(repository, lock_wait=None, local_path='borg', remote_path=None):
    '''
    Perform an extraction dry-run of the most recent archive. If there are no archives, skip the
    dry-run.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    lock_wait_flags = ('--lock-wait', str(lock_wait)) if lock_wait else ()
    verbosity_flags = ()
    if logger.isEnabledFor(logging.DEBUG):
        verbosity_flags = ('--debug', '--show-rc')
    elif logger.isEnabledFor(logging.INFO):
        verbosity_flags = ('--info',)

    full_list_command = (
        (local_path, 'list', '--short')
        + remote_path_flags
        + lock_wait_flags
        + verbosity_flags
        + (repository,)
    )

    list_output = execute_command(full_list_command, output_log_level=None)

    try:
        last_archive_name = list_output.strip().splitlines()[-1]
    except IndexError:
        return

    list_flag = ('--list',) if logger.isEnabledFor(logging.DEBUG) else ()
    full_extract_command = (
        (local_path, 'extract', '--dry-run')
        + remote_path_flags
        + lock_wait_flags
        + verbosity_flags
        + list_flag
        + (
            '{repository}::{last_archive_name}'.format(
                repository=repository, last_archive_name=last_archive_name
            ),
        )
    )

    execute_command(full_extract_command, working_directory=None, error_on_warnings=True)


def extract_archive(
    dry_run,
    repository,
    archive,
    paths,
    location_config,
    storage_config,
    local_path='borg',
    remote_path=None,
    destination_path=None,
    progress=False,
    error_on_warnings=True,
):
    '''
    Given a dry-run flag, a local or remote repository path, an archive name, zero or more paths to
    restore from the archive, location/storage configuration dicts, optional local and remote Borg
    paths, and an optional destination path to extract to, extract the archive into the current
    directory.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'extract')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--numeric-owner',) if location_config.get('numeric_owner') else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--list', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (('--progress',) if progress else ())
        + ('::'.join((repository if ':' in repository else os.path.abspath(repository), archive)),)
        + (tuple(paths) if paths else ())
    )

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    if progress:
        execute_command_without_capture(
            full_command, working_directory=destination_path, error_on_warnings=error_on_warnings
        )
        return

    # Error on warnings by default, as Borg only gives a warning if the restore paths don't exist in
    # the archive!
    execute_command(
        full_command, working_directory=destination_path, error_on_warnings=error_on_warnings
    )
