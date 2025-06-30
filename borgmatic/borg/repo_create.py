import argparse
import json
import logging
import shlex
import subprocess

import borgmatic.config.paths
from borgmatic.borg import environment, feature, flags, repo_info
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


REPO_INFO_REPOSITORY_NOT_FOUND_EXIT_CODES = {2, 13, 15}


def create_repository(
    dry_run,
    repository_path,
    config,
    local_borg_version,
    global_arguments,
    encryption_mode,
    source_repository=None,
    copy_crypt_key=False,
    append_only=None,
    storage_quota=None,
    make_parent_directories=False,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a dry-run flag, a local or remote repository path, a configuration dict, the local Borg
    version, a Borg encryption mode, the path to another repo whose key material should be reused,
    whether the repository should be append-only, and the storage quota to use, create the
    repository. If the repository already exists, then log and skip creation.

    Raise ValueError if the requested encryption mode does not match that of the repository.
    Raise json.decoder.JSONDecodeError if the "borg info" JSON outputcannot be decoded.
    Raise subprocess.CalledProcessError if "borg info" returns an error exit code.
    '''
    try:
        info_data = json.loads(
            repo_info.display_repository_info(
                repository_path,
                config,
                local_borg_version,
                argparse.Namespace(json=True),
                global_arguments,
                local_path,
                remote_path,
            )
        )
        repository_encryption_mode = info_data.get('encryption', {}).get('mode')

        if repository_encryption_mode != encryption_mode:
            raise ValueError(
                f'Requested encryption mode "{encryption_mode}" does not match existing repository encryption mode "{repository_encryption_mode}"'
            )

        logger.info('Repository already exists. Skipping creation.')
        return
    except subprocess.CalledProcessError as error:
        if error.returncode not in REPO_INFO_REPOSITORY_NOT_FOUND_EXIT_CODES:
            raise

    lock_wait = config.get('lock_wait')
    umask = config.get('umask')
    extra_borg_options = config.get('extra_borg_options', {}).get('repo-create', '')

    repo_create_command = (
        (local_path,)
        + (
            ('repo-create',)
            if feature.available(feature.Feature.REPO_CREATE, local_borg_version)
            else ('init',)
        )
        + (('--encryption', encryption_mode) if encryption_mode else ())
        + (('--other-repo', source_repository) if source_repository else ())
        + (('--copy-crypt-key',) if copy_crypt_key else ())
        + (('--append-only',) if append_only else ())
        + (('--storage-quota', storage_quota) if storage_quota else ())
        + (('--make-parent-dirs',) if make_parent_directories else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug',) if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (tuple(shlex.split(extra_borg_options)) if extra_borg_options else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    if dry_run:
        logging.info('Skipping repository creation (dry run)')
        return

    # Do not capture output here, so as to support interactive prompts.
    execute_command(
        repo_create_command,
        output_file=DO_NOT_CAPTURE,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
