import logging
import os
import subprocess

import borgmatic.config.paths
import borgmatic.config.validate
from borgmatic.borg import environment, feature, flags, repo_list
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def extract_last_archive_dry_run(
    config,
    local_borg_version,
    global_arguments,
    repository_path,
    lock_wait=None,
    local_path='borg',
    remote_path=None,
):
    '''
    Perform an extraction dry-run of the most recent archive. If there are no archives, skip the
    dry-run.
    '''
    verbosity_flags = ()
    if logger.isEnabledFor(logging.DEBUG):
        verbosity_flags = ('--debug', '--show-rc')
    elif logger.isEnabledFor(logging.INFO):
        verbosity_flags = ('--info',)

    try:
        last_archive_name = repo_list.resolve_archive_name(
            repository_path,
            'latest',
            config,
            local_borg_version,
            global_arguments,
            local_path,
            remote_path,
        )
    except ValueError:
        logger.warning('No archives found. Skipping extract consistency check.')
        return

    list_flag = ('--list',) if logger.isEnabledFor(logging.DEBUG) else ()
    full_extract_command = (
        (local_path, 'extract', '--dry-run')
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + verbosity_flags
        + list_flag
        + flags.make_repository_archive_flags(
            repository_path, last_archive_name, local_borg_version
        )
    )

    execute_command(
        full_extract_command,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )


def extract_archive(
    dry_run,
    repository,
    archive,
    paths,
    config,
    local_borg_version,
    global_arguments,
    local_path='borg',
    remote_path=None,
    destination_path=None,
    strip_components=None,
    extract_to_stdout=False,
):
    '''
    Given a dry-run flag, a local or remote repository path, an archive name, zero or more paths to
    restore from the archive, the local Borg version string, an argparse.Namespace of global
    arguments, a configuration dict, optional local and remote Borg paths, and an optional
    destination path to extract to, extract the archive into the current directory.

    If extract to stdout is True, then start the extraction streaming to stdout, and return that
    extract process as an instance of subprocess.Popen.
    '''
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)

    if config.get('progress') and extract_to_stdout:
        raise ValueError('progress and extract to stdout cannot both be set')

    if feature.available(feature.Feature.NUMERIC_IDS, local_borg_version):
        numeric_ids_flags = ('--numeric-ids',) if config.get('numeric_ids') else ()
    else:
        numeric_ids_flags = ('--numeric-owner',) if config.get('numeric_ids') else ()

    if strip_components == 'all':
        if not paths:
            raise ValueError('The --strip-components flag with "all" requires at least one --path')

        # Calculate the maximum number of leading path components of the given paths. "if piece"
        # ignores empty path components, e.g. those resulting from a leading slash. And the "- 1"
        # is so this doesn't count the final path component, e.g. the filename itself.
        strip_components = max(
            0,
            *(
                len(tuple(piece for piece in path.split(os.path.sep) if piece)) - 1
                for path in paths
            ),
        )

    working_directory = borgmatic.config.paths.get_working_directory(config)

    full_command = (
        (local_path, 'extract')
        + (('--remote-path', remote_path) if remote_path else ())
        + numeric_ids_flags
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--list', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (('--strip-components', str(strip_components)) if strip_components else ())
        + (('--progress',) if config.get('progress') else ())
        + (('--stdout',) if extract_to_stdout else ())
        + flags.make_repository_archive_flags(
            # Make the repository path absolute so the destination directory used below via changing
            # the working directory doesn't prevent Borg from finding the repo. But also apply the
            # user's configured working directory (if any) to the repo path.
            borgmatic.config.validate.normalize_repository_path(repository, working_directory),
            archive,
            local_borg_version,
        )
        + (tuple(paths) if paths else ())
    )

    borg_exit_codes = config.get('borg_exit_codes')
    full_destination_path = (
        os.path.join(working_directory or '', destination_path) if destination_path else None
    )

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    if config.get('progress'):
        return execute_command(
            full_command,
            output_file=DO_NOT_CAPTURE,
            environment=environment.make_environment(config),
            working_directory=full_destination_path,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
        return None

    if extract_to_stdout:
        return execute_command(
            full_command,
            output_file=subprocess.PIPE,
            run_to_completion=False,
            environment=environment.make_environment(config),
            working_directory=full_destination_path,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )

    # Don't give Borg local path so as to error on warnings, as "borg extract" only gives a warning
    # if the restore paths don't exist in the archive.
    execute_command(
        full_command,
        environment=environment.make_environment(config),
        working_directory=full_destination_path,
        borg_local_path=local_path,
        borg_exit_codes=borg_exit_codes,
    )
