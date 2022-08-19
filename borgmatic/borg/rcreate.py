import argparse
import logging
import subprocess

from borgmatic.borg import environment, feature, flags, rinfo
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


RINFO_REPOSITORY_NOT_FOUND_EXIT_CODE = 2


def create_repository(
    dry_run,
    repository,
    storage_config,
    local_borg_version,
    encryption_mode,
    source_repository=None,
    copy_crypt_key=False,
    append_only=None,
    storage_quota=None,
    make_parent_dirs=False,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a dry-run flag, a local or remote repository path, a storage configuration dict, the local
    Borg version, a Borg encryption mode, the path to another repo whose key material should be
    reused, whether the repository should be append-only, and the storage quota to use, create the
    repository. If the repository already exists, then log and skip creation.
    '''
    try:
        rinfo.display_repository_info(
            repository,
            storage_config,
            local_borg_version,
            argparse.Namespace(json=True),
            local_path,
            remote_path,
        )
        logger.info(f'{repository}: Repository already exists. Skipping creation.')
        return
    except subprocess.CalledProcessError as error:
        if error.returncode != RINFO_REPOSITORY_NOT_FOUND_EXIT_CODE:
            raise

    extra_borg_options = storage_config.get('extra_borg_options', {}).get('rcreate', '')

    rcreate_command = (
        (local_path,)
        + (
            ('rcreate',)
            if feature.available(feature.Feature.RCREATE, local_borg_version)
            else ('init',)
        )
        + (('--encryption', encryption_mode) if encryption_mode else ())
        + (('--other-repo', source_repository) if source_repository else ())
        + (('--copy-crypt-key',) if copy_crypt_key else ())
        + (('--append-only',) if append_only else ())
        + (('--storage-quota', storage_quota) if storage_quota else ())
        + (('--make-parent-dirs',) if make_parent_dirs else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug',) if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + flags.make_repository_flags(repository, local_borg_version)
    )

    if dry_run:
        logging.info(f'{repository}: Skipping repository creation (dry run)')
        return

    # Do not capture output here, so as to support interactive prompts.
    execute_command(
        rcreate_command,
        output_file=DO_NOT_CAPTURE,
        borg_local_path=local_path,
        extra_environment=environment.make_environment(storage_config),
    )
