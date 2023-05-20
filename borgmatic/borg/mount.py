import logging

from borgmatic.borg import environment, feature, flags
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def mount_archive(
    repository_path,
    archive,
    mount_arguments,
    storage_config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, an optional archive name, a filesystem mount point,
    zero or more paths to mount from the archive, extra Borg mount options, a storage configuration
    dict, the local Borg version, global arguments as an argparse.Namespace instance, and optional
    local and remote Borg paths, mount the archive onto the mount point.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'mount')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if global_arguments.log_json else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_flags_from_arguments(
            mount_arguments,
            excludes=('repository', 'archive', 'mount_point', 'paths', 'options'),
        )
        + (('-o', mount_arguments.options) if mount_arguments.options else ())
        + (
            (
                flags.make_repository_flags(repository_path, local_borg_version)
                + (
                    ('--match-archives', archive)
                    if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version)
                    else ('--glob-archives', archive)
                )
            )
            if feature.available(feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, local_borg_version)
            else (
                flags.make_repository_archive_flags(repository_path, archive, local_borg_version)
                if archive
                else flags.make_repository_flags(repository_path, local_borg_version)
            )
        )
        + (mount_arguments.mount_point,)
        + (tuple(mount_arguments.paths) if mount_arguments.paths else ())
    )

    borg_environment = environment.make_environment(storage_config)

    # Don't capture the output when foreground mode is used so that ctrl-C can work properly.
    if mount_arguments.foreground:
        execute_command(
            full_command,
            output_file=DO_NOT_CAPTURE,
            borg_local_path=local_path,
            extra_environment=borg_environment,
        )
        return

    execute_command(full_command, borg_local_path=local_path, extra_environment=borg_environment)
