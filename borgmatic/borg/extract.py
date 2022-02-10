import logging
import os
import subprocess

from borgmatic.borg import feature
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

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

    list_output = execute_command(
        full_list_command, output_log_level=None, borg_local_path=local_path
    )

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

    execute_command(full_extract_command, working_directory=None)


def extract_archive(
    dry_run,
    repository,
    archive,
    paths,
    location_config,
    storage_config,
    local_borg_version,
    local_path='borg',
    remote_path=None,
    destination_path=None,
    strip_components=None,
    progress=False,
    extract_to_stdout=False,
):
    '''
    Given a dry-run flag, a local or remote repository path, an archive name, zero or more paths to
    restore from the archive, the local Borg version string, location/storage configuration dicts,
    optional local and remote Borg paths, and an optional destination path to extract to, extract
    the archive into the current directory.

    If extract to stdout is True, then start the extraction streaming to stdout, and return that
    extract process as an instance of subprocess.Popen.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    if progress and extract_to_stdout:
        raise ValueError('progress and extract_to_stdout cannot both be set')

    if feature.available(feature.Feature.NUMERIC_IDS, local_borg_version):
        numeric_ids_flags = ('--numeric-ids',) if location_config.get('numeric_owner') else ()
    else:
        numeric_ids_flags = ('--numeric-owner',) if location_config.get('numeric_owner') else ()

    full_command = (
        (local_path, 'extract')
        + (('--remote-path', remote_path) if remote_path else ())
        + numeric_ids_flags
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--list', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (('--strip-components', str(strip_components)) if strip_components else ())
        + (('--progress',) if progress else ())
        + (('--stdout',) if extract_to_stdout else ())
        + ('::'.join((repository if ':' in repository else os.path.abspath(repository), archive)),)
        + (tuple(paths) if paths else ())
    )

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    if progress:
        return execute_command(
            full_command, output_file=DO_NOT_CAPTURE, working_directory=destination_path
        )
        return None

    if extract_to_stdout:
        return execute_command(
            full_command,
            output_file=subprocess.PIPE,
            working_directory=destination_path,
            run_to_completion=False,
        )

    # Don't give Borg local path, so as to error on warnings, as Borg only gives a warning if the
    # restore paths don't exist in the archive!
    execute_command(full_command, working_directory=destination_path)
