import logging
import subprocess

from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


INFO_REPOSITORY_NOT_FOUND_EXIT_CODE = 2


def initialize_repository(
    repository,
    storage_config,
    encryption_mode,
    append_only=None,
    storage_quota=None,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a storage configuration dict, a Borg encryption mode,
    whether the repository should be append-only, and the storage quota to use, initialize the
    repository. If the repository already exists, then log and skip initialization.
    '''
    info_command = (
        (local_path, 'info')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug',) if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (repository,)
    )
    logger.debug(' '.join(info_command))

    try:
        execute_command(info_command, output_log_level=None)
        logger.info('Repository already exists. Skipping initialization.')
        return
    except subprocess.CalledProcessError as error:
        if error.returncode != INFO_REPOSITORY_NOT_FOUND_EXIT_CODE:
            raise

    extra_borg_options = storage_config.get('extra_borg_options', {}).get('init', '')

    init_command = (
        (local_path, 'init')
        + (('--encryption', encryption_mode) if encryption_mode else ())
        + (('--append-only',) if append_only else ())
        + (('--storage-quota', storage_quota) if storage_quota else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug',) if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + (repository,)
    )

    # Do not capture output here, so as to support interactive prompts.
    execute_command(init_command, output_file=DO_NOT_CAPTURE, borg_local_path=local_path)
