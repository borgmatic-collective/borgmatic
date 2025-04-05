import logging
import os

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, flags
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def export_key(
    repository_path,
    config,
    local_borg_version,
    export_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, export
    arguments, and optional local and remote Borg paths, export the repository key to the
    destination path indicated in the export arguments.

    If the destination path is empty or "-", then print the key to stdout instead of to a file.

    Raise FileExistsError if a path is given but it already exists on disk.
    '''
    borgmatic.logger.add_custom_log_levels()
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)
    working_directory = borgmatic.config.paths.get_working_directory(config)

    if export_arguments.path and export_arguments.path != '-':
        if os.path.exists(os.path.join(working_directory or '', export_arguments.path)):
            raise FileExistsError(
                f'Destination path {export_arguments.path} already exists. Aborting.'
            )

        output_file = None
    else:
        output_file = DO_NOT_CAPTURE

    full_command = (
        (local_path, 'key', 'export')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_flags('paper', export_arguments.paper)
        + flags.make_flags('qr-html', export_arguments.qr_html)
        + flags.make_repository_flags(
            repository_path,
            local_borg_version,
        )
        + ((export_arguments.path,) if output_file is None else ())
    )

    if global_arguments.dry_run:
        logger.info('Skipping key export (dry run)')
        return

    execute_command(
        full_command,
        output_file=output_file,
        output_log_level=logging.ANSWER,
        environment=environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
