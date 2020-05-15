import logging

from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def unmount_archive(mount_point, local_path='borg'):
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

    execute_command(full_command)
