import logging
import os

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, flags
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def import_key(
    repository_path,
    config,
    local_borg_version,
    import_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, import
    arguments, and optional local and remote Borg paths, import the repository key from the
    path indicated in the import arguments.

    If the path is empty or "-", then read the key from stdin.

    Raise ValueError if the path is given and it does not exist.
    '''
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)
    working_directory = borgmatic.config.paths.get_working_directory(config)

    if import_arguments.path and import_arguments.path != '-':
        if not os.path.exists(os.path.join(working_directory or '', import_arguments.path)):
            raise ValueError(f'Path {import_arguments.path} does not exist. Aborting.')

        input_file = None
    else:
        input_file = DO_NOT_CAPTURE

    full_command = (
        (local_path, 'key', 'import')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + flags.make_flags('paper', import_arguments.paper)
        + flags.make_repository_flags(
            repository_path,
            local_borg_version,
        )
        + ((import_arguments.path,) if input_file is None else ())
    )

    if global_arguments.dry_run:
        logger.info('Skipping key import (dry run)')
        return

    execute_command(
        full_command,
        input_file=input_file,
        output_log_level=logging.INFO,
        environment=environment.make_environment(config),
        working_directory=working_directory,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
