import logging
import os

from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def export_tar_archive(
    dry_run,
    repository,
    archive,
    paths,
    destination_path,
    storage_config,
    local_path='borg',
    remote_path=None,
    tar_filter=None,
    files=False,
    strip_components=None,
):
    '''
    Given a dry-run flag, a local or remote repository path, an archive name, zero or more paths to
    export from the archive, a destination path to export to, a storage configuration dict, optional
    local and remote Borg paths, an optional filter program, whether to include per-file details,
    and an optional number of path components to strip, export the archive into the given
    destination path as a tar-formatted file.

    If the destination path is "-", then stream the output to stdout instead of to a file.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'export-tar')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--list',) if files else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (('--tar-filter', tar_filter) if tar_filter else ())
        + (('--strip-components', str(strip_components)) if strip_components else ())
        + ('::'.join((repository if ':' in repository else os.path.abspath(repository), archive)),)
        + (destination_path,)
        + (tuple(paths) if paths else ())
    )

    if files and logger.getEffectiveLevel() == logging.WARNING:
        output_log_level = logging.WARNING
    else:
        output_log_level = logging.INFO

    if dry_run:
        logging.info('{}: Skipping export to tar file (dry run)'.format(repository))
        return

    execute_command(
        full_command,
        output_file=DO_NOT_CAPTURE if destination_path == '-' else None,
        output_log_level=output_log_level,
        borg_local_path=local_path,
    )
