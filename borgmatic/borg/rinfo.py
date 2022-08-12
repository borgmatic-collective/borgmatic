import logging

from borgmatic.borg import environment, feature
from borgmatic.borg.flags import make_flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def display_repository_info(
    repository,
    storage_config,
    local_borg_version,
    rinfo_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a storage config dict, the local Borg version, and the
    arguments to the rinfo action, display summary information for the Borg repository or return
    JSON summary information.
    '''
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path,)
        + (
            ('rinfo',)
            if feature.available(feature.Feature.RINFO, local_borg_version)
            else ('info',)
        )
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not rinfo_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not rinfo_arguments.json
            else ()
        )
        + make_flags('remote-path', remote_path)
        + make_flags('lock-wait', lock_wait)
        + (('--json',) if rinfo_arguments.json else ())
        + (
            ('--repo',)
            if feature.available(feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, local_borg_version)
            else ()
        )
        + (repository,)
    )

    return execute_command(
        full_command,
        output_log_level=None if rinfo_arguments.json else logging.WARNING,
        borg_local_path=local_path,
        extra_environment=environment.make_environment(storage_config),
    )
