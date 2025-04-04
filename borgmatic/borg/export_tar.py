import logging

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, flags
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def export_tar_archive(
    dry_run,
    repository_path,
    archive,
    paths,
    destination_path,
    config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
    tar_filter=None,
    strip_components=None,
):
    '''
    Given a dry-run flag, a local or remote repository path, an archive name, zero or more paths to
    export from the archive, a destination path to export to, a configuration dict, the local Borg
    version, optional local and remote Borg paths, an optional filter program, whether to include
    per-file details, and an optional number of path components to strip, export the archive into
    the given destination path as a tar-formatted file.

    If the destination path is "-", then stream the output to stdout instead of to a file.
    '''
    borgmatic.logger.add_custom_log_levels()
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)

    full_command = (
        (local_path, 'export-tar')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--list',) if config.get('list_details') else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (('--tar-filter', tar_filter) if tar_filter else ())
        + (('--strip-components', str(strip_components)) if strip_components else ())
        + flags.make_repository_archive_flags(
            repository_path,
            archive,
            local_borg_version,
        )
        + (destination_path,)
        + (tuple(paths) if paths else ())
    )

    if config.get('list_details'):
        output_log_level = logging.ANSWER
    else:
        output_log_level = logging.INFO

    if dry_run:
        logging.info('Skipping export to tar file (dry run)')
        return

    execute_command(
        full_command,
        output_file=DO_NOT_CAPTURE if destination_path == '-' else None,
        output_log_level=output_log_level,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
