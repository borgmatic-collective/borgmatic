import logging

from borgmatic.borg.flags import make_flags, make_flags_from_arguments
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def display_archives_info(
    repository, storage_config, info_arguments, local_path='borg', remote_path=None
):
    '''
    Given a local or remote repository path, a storage config dict, and the arguments to the info
    action, display summary information for Borg archives in the repository or return JSON summary
    information.
    '''
    lock_wait = storage_config.get('lock_wait', None)

    full_command = (
        (local_path, 'info')
        + (
            ('--info',)
            if logger.getEffectiveLevel() == logging.INFO and not info_arguments.json
            else ()
        )
        + (
            ('--debug', '--show-rc')
            if logger.isEnabledFor(logging.DEBUG) and not info_arguments.json
            else ()
        )
        + make_flags('remote-path', remote_path)
        + make_flags('lock-wait', lock_wait)
        + make_flags_from_arguments(info_arguments, excludes=('repository', 'archive'))
        + (
            '::'.join((repository, info_arguments.archive))
            if info_arguments.archive
            else repository,
        )
    )

    return execute_command(
        full_command,
        output_log_level=None if info_arguments.json else logging.WARNING,
        borg_local_path=local_path,
    )
