import logging
import os
import pathlib
import shlex
import stat
import textwrap

import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import (
    DO_NOT_CAPTURE,
    execute_command,
    execute_command_and_capture_output,
    execute_command_with_processes,
)

logger = logging.getLogger(__name__)


def special_file(path, working_directory=None):
    '''
    Return whether the given path is a special file (character device, block device, or named pipe
    / FIFO). If a working directory is given, take it into account when making the full path to
    check.
    '''
    try:
        mode = os.stat(os.path.join(working_directory or '', path)).st_mode
    except (FileNotFoundError, OSError):
        return False

    return stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode)


def any_parent_directories(path, candidate_parents):
    '''
    Return whether any of the given candidate parent directories are an actual parent of the given
    path. This includes grandparents, etc.
    '''
    for parent in candidate_parents:
        if pathlib.PurePosixPath(parent) in pathlib.PurePath(path).parents:
            return True

    return False


def validate_planned_backup_paths(
    dry_run,
    create_command,
    config,
    patterns,
    local_path,
    working_directory,
    borgmatic_runtime_directory,
    find_special_files=False,
):
    '''
    Given a dry-run flag, a Borg create command as a tuple, a configuration dict, a local Borg path,
    a working directory, and the borgmatic runtime directory, perform a "borg create --dry-run" to
    determine whether Borg's planned paths to include in a backup look good. Specifically, if the
    given runtime directory exists, validate that it will be included in a backup and hasn't been
    excluded.

    If find special files is True, then return the subset of planned backup paths that are special
    files. Otherwise, return an empty tuple.

    Raise ValueError if the runtime directory has been excluded via "exclude_patterns" or similar,
    because any features that rely on the runtime directory getting backed up will break. For
    instance, without the runtime directory, Borg can't consume any database dumps and borgmatic may
    hang waiting for them to be consumed.
    '''
    # Omit "--exclude-nodump" from the Borg dry run command, because that flag causes Borg to open
    # files including any named pipe we've created. And omit "--filter" because that can break the
    # paths output parsing below such that path lines no longer start with the expected "- ".
    path_lines = execute_command_and_capture_output(
        (
            *flags.omit_flag_and_value(
                flags.omit_flag(
                    flags.omit_flag(create_command, '--exclude-nodump'),
                    '--log-json',
                ),
                '--filter',
            ),
            '--dry-run',
            '--list',
        ),
        capture_stderr=True,
        working_directory=working_directory,
        environment=environment.make_environment(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    # These are all the individual files that Borg is planning to backup as determined by the Borg
    # create dry run above.
    paths = (
        path_line.split(' ', 1)[1]
        for path_line in path_lines
        if path_line and path_line.startswith(('- ', '+ '))
    )

    include_pattern_paths = {
        pattern.path
        for pattern in patterns
        if pattern.type == borgmatic.borg.pattern.Pattern_type.INCLUDE
    }
    runtime_directory_root_patterns = tuple(
        pattern
        for pattern in patterns
        if any_parent_directories(pattern.path, (borgmatic_runtime_directory,))
        if pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
        # Skip root patterns that have corresponding include patterns, because those will "punch
        # through" any subsequent excludes.
        if pattern.path not in include_pattern_paths
    )

    special_paths = []
    runtime_directory_exists = os.path.exists(borgmatic_runtime_directory)
    candidate_for_warning = bool(
        not dry_run and runtime_directory_exists and runtime_directory_root_patterns
    )

    # Do everything in this one loop because we only want to consume the paths generator once.
    for path in paths:
        # If all root patterns in the runtime directory are missing from the paths Borg is planning to
        # backup, then they must've gotten excluded, e.g. by user-configured excludes. Warn accordingly.
        if candidate_for_warning and not any(
            any_parent_directories(path, (pattern.path,))
            for pattern in runtime_directory_root_patterns
        ):
            logger.warning(
                f'The runtime directory {os.path.normpath(borgmatic_runtime_directory)} overlaps with the configured excludes (or the snapshotted source directories are empty). Please ensure the runtime directory is not excluded.'
            )
            candidate_for_warning = False

        # Return the subset of output paths that are special files but *not* contained within the
        # borgmatic runtime directory. The intent is to skip runtime paths that borgmatic uses for its
        # own bookkeeping, instead focusing on user-configured paths.
        if not any_parent_directories(path, (borgmatic_runtime_directory,)) and special_file(
            path, working_directory
        ):
            special_paths.append(path)

    return tuple(special_paths)


MAX_SPECIAL_FILE_PATHS_LENGTH = 1000


def make_base_create_command(  # noqa: PLR0912
    dry_run,
    repository_path,
    config,
    patterns,
    local_borg_version,
    global_arguments,
    borgmatic_runtime_directory,
    archive_suffix='',
    local_path='borg',
    remote_path=None,
    json=False,
    comment=None,
    stream_processes=None,
):
    '''
    Given verbosity/dry-run flags, a local or remote repository path, a configuration dict, a
    sequence of patterns as borgmatic.borg.pattern.Pattern instances, the local Borg version, global
    arguments as an argparse.Namespace instance, the borgmatic runtime directory, a string suffix to
    add to the archive name, the local Borg path, the remote Borg path, whether to output JSON,
    comment text to add to the created archive, and a sequence of processes streaming data to Borg,
    return a tuple of (base Borg create command flags, Borg create command positional arguments,
    open pattern file handle).
    '''
    if config.get('source_directories_must_exist', False):
        borgmatic.borg.pattern.check_all_root_patterns_exist(patterns)

    patterns_file = borgmatic.borg.pattern.write_patterns_file(
        patterns,
        borgmatic_runtime_directory,
    )
    checkpoint_interval = config.get('checkpoint_interval', None)
    checkpoint_volume = config.get('checkpoint_volume', None)
    chunker_params = config.get('chunker_params', None)
    compression = config.get('compression', None)
    upload_rate_limit = config.get('upload_rate_limit', None)
    upload_buffer_size = config.get('upload_buffer_size', None)
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)
    list_filter_flags = flags.make_list_filter_flags(local_borg_version, dry_run)
    files_cache = config.get('files_cache')
    archive_name_format = (
        config.get('archive_name_format', flags.get_default_archive_name_format(local_borg_version))
        + archive_suffix
    )
    extra_borg_options = config.get('extra_borg_options', {}).get('create', '')

    if feature.available(feature.Feature.ATIME, local_borg_version):
        atime_flags = ('--atime',) if config.get('atime') is True else ()
    else:
        atime_flags = ('--noatime',) if config.get('atime') is False else ()

    if feature.available(feature.Feature.NOFLAGS, local_borg_version):
        noflags_flags = ('--noflags',) if config.get('flags') is False else ()
    else:
        noflags_flags = ('--nobsdflags',) if config.get('flags') is False else ()

    if feature.available(feature.Feature.NUMERIC_IDS, local_borg_version):
        numeric_ids_flags = ('--numeric-ids',) if config.get('numeric_ids') else ()
    else:
        numeric_ids_flags = ('--numeric-owner',) if config.get('numeric_ids') else ()

    if feature.available(feature.Feature.UPLOAD_RATELIMIT, local_borg_version):
        upload_ratelimit_flags = (
            ('--upload-ratelimit', str(upload_rate_limit)) if upload_rate_limit else ()
        )
    else:
        upload_ratelimit_flags = (
            ('--remote-ratelimit', str(upload_rate_limit)) if upload_rate_limit else ()
        )

    create_flags = (
        tuple(local_path.split(' '))
        + ('create',)
        + (('--patterns-from', patterns_file.name) if patterns_file else ())
        + flags.make_exclude_flags(config)
        + (('--comment', comment) if comment else ())
        + (('--checkpoint-interval', str(checkpoint_interval)) if checkpoint_interval else ())
        + (('--checkpoint-volume', str(checkpoint_volume)) if checkpoint_volume else ())
        + (('--chunker-params', chunker_params) if chunker_params else ())
        + (('--compression', compression) if compression else ())
        + upload_ratelimit_flags
        + (('--upload-buffer', str(upload_buffer_size)) if upload_buffer_size else ())
        + (('--one-file-system',) if config.get('one_file_system') else ())
        + numeric_ids_flags
        + atime_flags
        + (('--noctime',) if config.get('ctime') is False else ())
        + (('--nobirthtime',) if config.get('birthtime') is False else ())
        + (('--read-special',) if config.get('read_special') or stream_processes else ())
        + noflags_flags
        + (('--files-cache', files_cache) if files_cache else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--log-json',) if (config.get('log_json') or not config.get('progress')) else ())
        + (
            ('--list', '--filter', list_filter_flags)
            if config.get('list_details') and not json and not config.get('progress')
            else ()
        )
        + (('--dry-run',) if dry_run else ())
        + (tuple(shlex.split(extra_borg_options)) if extra_borg_options else ())
    )

    create_positional_arguments = flags.make_repository_archive_flags(
        repository_path,
        archive_name_format,
        local_borg_version,
    )
    working_directory = borgmatic.config.paths.get_working_directory(config)

    if config.get('unsafe_skip_path_validation_before_create'):
        logger.warning(
            'Skipping pre-backup path validation due to "unsafe_skip_path_validation_before_create" option.'
        )

        return (create_flags, create_positional_arguments, patterns_file)

    logger.debug('Checking file paths Borg plans to include')

    special_file_paths = validate_planned_backup_paths(
        dry_run,
        create_flags + create_positional_arguments,
        config,
        patterns,
        local_path,
        working_directory,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
        find_special_files=bool(stream_processes and not config.get('read_special')),
    )

    # If database hooks are enabled (as indicated by streaming processes), exclude files that might
    # cause Borg to hang. But skip this if the user has explicitly set the "read_special" to True.
    if special_file_paths:
        logger.warning(
            'Ignoring configured "read_special" value of false, as true is needed for database hooks.',
        )

        truncated_special_file_paths = textwrap.shorten(
            ', '.join(special_file_paths),
            width=MAX_SPECIAL_FILE_PATHS_LENGTH,
            placeholder=' ...',
        )
        logger.warning(
            f'Excluding special files to prevent Borg from hanging: {truncated_special_file_paths}',
        )
        patterns_file = borgmatic.borg.pattern.write_patterns_file(
            tuple(
                borgmatic.borg.pattern.Pattern(
                    special_file_path,
                    borgmatic.borg.pattern.Pattern_type.NO_RECURSE,
                    borgmatic.borg.pattern.Pattern_style.FNMATCH,
                    source=borgmatic.borg.pattern.Pattern_source.INTERNAL,
                )
                for special_file_path in special_file_paths
            ),
            borgmatic_runtime_directory,
            patterns_file=patterns_file,
        )

        if '--patterns-from' not in create_flags:
            create_flags += ('--patterns-from', patterns_file.name)

    return (create_flags, create_positional_arguments, patterns_file)


def create_archive(
    dry_run,
    repository_path,
    config,
    patterns,
    local_borg_version,
    global_arguments,
    borgmatic_runtime_directory,
    archive_suffix='',
    local_path='borg',
    remote_path=None,
    json=False,
    comment=None,
    stream_processes=None,
):
    '''
    Given verbosity/dry-run flags, a local or remote repository path, a configuration dict, a
    sequence of loaded configuration paths, the local Borg version, global arguments as an
    argparse.Namespace instance, the borgmatic runtime directory, a string suffix to add to the
    archive name, the local Borg path, the remote Borg path, whether to output JSON, and comment
    text to add to the created archive, and a sequence of processes streaming data to Borg, create a
    Borg archive and return Borg's JSON output (if any).

    If a sequence of stream processes is given (instances of subprocess.Popen), then execute the
    create command while also triggering the given processes to produce output.
    '''
    borgmatic.logger.add_custom_log_levels()

    working_directory = borgmatic.config.paths.get_working_directory(config)

    (create_flags, create_positional_arguments, _) = make_base_create_command(
        dry_run,
        repository_path,
        config,
        patterns,
        local_borg_version,
        global_arguments,
        borgmatic_runtime_directory,
        archive_suffix,
        local_path,
        remote_path,
        json,
        comment,
        stream_processes,
    )

    if json:
        output_log_level = None
    elif config.get('list_details') or (config.get('statistics') and not dry_run):
        output_log_level = logging.ANSWER
    else:
        output_log_level = logging.INFO

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    output_file = DO_NOT_CAPTURE if config.get('progress') else None

    create_flags += (
        (('--info',) if logger.getEffectiveLevel() == logging.INFO and not json else ())
        + (('--stats',) if config.get('statistics') and not json and not dry_run else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) and not json else ())
        + (('--progress',) if config.get('progress') else ())
        + (('--json',) if json else ())
    )
    borg_exit_codes = config.get('borg_exit_codes')

    if stream_processes:
        return execute_command_with_processes(
            create_flags + create_positional_arguments,
            stream_processes,
            output_log_level,
            output_file,
            working_directory=working_directory,
            environment=environment.make_environment(config),
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )

    if output_log_level is None:
        return '\n'.join(
            execute_command_and_capture_output(
                create_flags + create_positional_arguments,
                working_directory=working_directory,
                environment=environment.make_environment(config),
                borg_local_path=local_path,
                borg_exit_codes=borg_exit_codes,
            )
        )

    execute_command(
        create_flags + create_positional_arguments,
        output_log_level,
        output_file,
        working_directory=working_directory,
        environment=environment.make_environment(config),
        borg_local_path=local_path,
        borg_exit_codes=borg_exit_codes,
    )

    return None
