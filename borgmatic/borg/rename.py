import logging
import shlex

import borgmatic.borg.flags

logger = logging.getLogger(__name__)


def make_rename_command(
    dry_run,
    repository_name,
    old_archive_name,
    new_archive_name,
    config,
    local_borg_version,
    local_path,
    remote_path,
):
    extra_borg_options = config.get('extra_borg_options', {}).get('rename', '')

    return (
        (local_path, 'rename')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + borgmatic.borg.flags.make_flags('dry-run', dry_run)
        + borgmatic.borg.flags.make_flags('remote-path', remote_path)
        + borgmatic.borg.flags.make_flags('umask', config.get('umask'))
        + ('--log-json',)
        + borgmatic.borg.flags.make_flags('lock-wait', config.get('lock_wait'))
        + (tuple(shlex.split(extra_borg_options)) if extra_borg_options else ())
        + borgmatic.borg.flags.make_repository_archive_flags(
            repository_name,
            old_archive_name,
            local_borg_version,
        )
        + (new_archive_name,)
    )


def rename_archive(
    repository_name,
    old_archive_name,
    new_archive_name,
    dry_run,
    config,
    local_borg_version,
    local_path,
    remote_path,
):
    command = make_rename_command(
        dry_run,
        repository_name,
        old_archive_name,
        new_archive_name,
        config,
        local_borg_version,
        local_path,
        remote_path,
    )

    borgmatic.execute.execute_command(
        command,
        output_log_level=logging.INFO,
        environment=borgmatic.borg.environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
