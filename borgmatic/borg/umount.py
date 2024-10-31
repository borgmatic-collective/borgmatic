import logging

import borgmatic.config.paths
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def unmount_archive(config, mount_point, local_path='borg'):
    '''
    Given a mounted filesystem mount point, and an optional local Borg paths, umount the filesystem
    from the mount point.
    '''
    full_command = (
        (local_path, 'umount')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (mount_point,)
    )

    execute_command(
        full_command,
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
