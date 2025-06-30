import logging
import shlex

import borgmatic.config.paths
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def compact_segments(
    dry_run,
    repository_path,
    config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
    cleanup_commits=False,
):
    '''
    Given dry-run flag, a local or remote repository path, a configuration dict, and the local Borg
    version, compact the segments in a repository.
    '''
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)
    extra_borg_options = config.get('extra_borg_options', {}).get('compact', '')
    threshold = config.get('compact_threshold')

    full_command = (
        (local_path, 'compact')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--progress',) if config.get('progress') else ())
        + (('--cleanup-commits',) if cleanup_commits else ())
        + (('--threshold', str(threshold)) if threshold else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (
            ('--dry-run',)
            if dry_run and feature.available(feature.Feature.DRY_RUN_COMPACT, local_borg_version)
            else ()
        )
        + (tuple(shlex.split(extra_borg_options)) if extra_borg_options else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    if dry_run and not feature.available(feature.Feature.DRY_RUN_COMPACT, local_borg_version):
        logging.info('Skipping compact (dry run)')
        return

    execute_command(
        full_command,
        output_log_level=logging.INFO,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
