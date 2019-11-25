import logging

from borgmatic.execute import execute_command, execute_command_without_capture

logger = logging.getLogger(__name__)


def mount_archive(
    repository,
    archive,
    mount_point,
    paths,
    foreground,
    options,
    storage_config,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, an archive name, a filesystem mount point, zero or more
    paths to mount from the archive, extra Borg mount options, a storage configuration dict, and
    optional local and remote Borg paths, mount the archive onto the mount point.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'mount')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--foreground',) if foreground else ())
        + (('-o', options) if options else ())
        + ('::'.join((repository, archive)),)
        + (mount_point,)
        + (tuple(paths) if paths else ())
    )

    # Don't capture the output when foreground mode is used so that ctrl-C can work properly.
    if foreground:
        execute_command_without_capture(full_command)
        return

    execute_command(full_command)
