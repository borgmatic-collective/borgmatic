import logging

from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def compact_segments(
    dry_run,
    repository,
    storage_config,
    local_path='borg',
    remote_path=None,
    progress=False,
    cleanup_commits=False,
    threshold=None,
):
    '''
    Given dry-run flag, a local or remote repository path, and a storage config dict, compact Borg
    segments in a repository.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)
    extra_borg_options = storage_config.get('extra_borg_options', {}).get('compact', '')

    full_command = (
        (local_path, 'compact')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--progress',) if progress else ())
        + (('--cleanup-commits',) if cleanup_commits else ())
        + (('--threshold', str(threshold)) if threshold else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + (repository,)
    )

    if not dry_run:
        execute_command(full_command, output_log_level=logging.INFO, borg_local_path=local_path)
