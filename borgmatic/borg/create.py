import itertools
import logging
import os
import pathlib
import stat
import tempfile
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


def write_patterns_file(patterns, borgmatic_runtime_directory, patterns_file=None):
    '''
    Given a sequence of patterns as borgmatic.borg.pattern.Pattern instances, write them to a named
    temporary file in the given borgmatic runtime directory and return the file object so it can
    continue to exist on disk as long as the caller needs it.

    If an optional open pattern file is given, append to it instead of making a new temporary file.
    Return None if no patterns are provided.
    '''
    if not patterns:
        return None

    if patterns_file is None:
        patterns_file = tempfile.NamedTemporaryFile('w', dir=borgmatic_runtime_directory)
        operation_name = 'Writing'
    else:
        patterns_file.write('\n')
        operation_name = 'Appending'

    patterns_output = '\n'.join(
        f'{pattern.type.value} {pattern.style.value}{":" if pattern.style.value else ""}{pattern.path}'
        for pattern in patterns
    )
    logger.debug(f'{operation_name} patterns to {patterns_file.name}:\n{patterns_output}')

    patterns_file.write(patterns_output)
    patterns_file.flush()

    return patterns_file


def make_exclude_flags(config):
    '''
    Given a configuration dict with various exclude options, return the corresponding Borg flags as
    a tuple.
    '''
    caches_flag = ('--exclude-caches',) if config.get('exclude_caches') else ()
    if_present_flags = tuple(
        itertools.chain.from_iterable(
            ('--exclude-if-present', if_present)
            for if_present in config.get('exclude_if_present', ())
        )
    )
    keep_exclude_tags_flags = ('--keep-exclude-tags',) if config.get('keep_exclude_tags') else ()
    exclude_nodump_flags = ('--exclude-nodump',) if config.get('exclude_nodump') else ()

    return caches_flag + if_present_flags + keep_exclude_tags_flags + exclude_nodump_flags


def make_list_filter_flags(local_borg_version, dry_run):
    '''
    Given the local Borg version and whether this is a dry run, return the corresponding flags for
    passing to "--list --filter". The general idea is that excludes are shown for a dry run or when
    the verbosity is debug.
    '''
    base_flags = 'AME'
    show_excludes = logger.isEnabledFor(logging.DEBUG)

    if feature.available(feature.Feature.EXCLUDED_FILES_MINUS, local_borg_version):
        if show_excludes or dry_run:
            return f'{base_flags}+-'
        else:
            return base_flags

    if show_excludes:
        return f'{base_flags}x-'
    else:
        return f'{base_flags}-'


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


def collect_special_file_paths(
    dry_run,
    create_command,
    config,
    local_path,
    working_directory,
    borgmatic_runtime_directory,
):
    '''
    Given a dry-run flag, a Borg create command as a tuple, a configuration dict, a local Borg path,
    a working directory, and the borgmatic runtime directory, collect the paths for any special
    files (character devices, block devices, and named pipes / FIFOs) that Borg would encounter
    during a create. These are all paths that could cause Borg to hang if its --read-special flag is
    used.

    Skip looking for special files in the given borgmatic runtime directory, as borgmatic creates
    its own special files there for database dumps and we don't want those omitted.

    Additionally, if the borgmatic runtime directory is not contained somewhere in the files Borg
    plans to backup, that means the user must have excluded the runtime directory (e.g. via
    "exclude_patterns" or similar). Therefore, raise, because this means Borg won't be able to
    consume any database dumps and therefore borgmatic will hang when it tries to do so.
    '''
    # Omit "--exclude-nodump" from the Borg dry run command, because that flag causes Borg to open
    # files including any named pipe we've created. And omit "--filter" because that can break the
    # paths output parsing below such that path lines no longer start with th expected "- ".
    paths_output = execute_command_and_capture_output(
        flags.omit_flag_and_value(flags.omit_flag(create_command, '--exclude-nodump'), '--filter')
        + ('--dry-run', '--list'),
        capture_stderr=True,
        working_directory=working_directory,
        environment=environment.make_environment(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    # These are all the individual files that Borg is planning to backup as determined by the Borg
    # create dry run above.
    paths = tuple(
        path_line.split(' ', 1)[1]
        for path_line in paths_output.split('\n')
        if path_line and path_line.startswith('- ') or path_line.startswith('+ ')
    )

    # These are the subset of those files that contain the borgmatic runtime directory.
    paths_containing_runtime_directory = {}

    if os.path.exists(borgmatic_runtime_directory):
        paths_containing_runtime_directory = {
            path for path in paths if any_parent_directories(path, (borgmatic_runtime_directory,))
        }

        # If no paths to backup contain the runtime directory, it must've been excluded.
        if not paths_containing_runtime_directory and not dry_run:
            raise ValueError(
                f'The runtime directory {os.path.normpath(borgmatic_runtime_directory)} overlaps with the configured excludes or patterns with excludes. Please ensure the runtime directory is not excluded.'
            )

    return tuple(
        path
        for path in paths
        if special_file(path, working_directory)
        if path not in paths_containing_runtime_directory
    )


def check_all_root_patterns_exist(patterns):
    '''
    Given a sequence of borgmatic.borg.pattern.Pattern instances, check that all root pattern
    paths exist. If any don't, raise an exception.
    '''
    missing_paths = [
        pattern.path
        for pattern in patterns
        if pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
        if not os.path.exists(pattern.path)
    ]

    if missing_paths:
        raise ValueError(
            f"Source directories / root pattern paths do not exist: {', '.join(missing_paths)}"
        )


MAX_SPECIAL_FILE_PATHS_LENGTH = 1000


def make_base_create_command(
    dry_run,
    repository_path,
    config,
    patterns,
    local_borg_version,
    global_arguments,
    borgmatic_runtime_directory,
    local_path='borg',
    remote_path=None,
    progress=False,
    json=False,
    list_files=False,
    stream_processes=None,
):
    '''
    Given verbosity/dry-run flags, a local or remote repository path, a configuration dict, a
    sequence of patterns as borgmatic.borg.pattern.Pattern instances, the local Borg version,
    global arguments as an argparse.Namespace instance, and a sequence of borgmatic source
    directories, return a tuple of (base Borg create command flags, Borg create command positional
    arguments, open pattern file handle).
    '''
    if config.get('source_directories_must_exist', False):
        check_all_root_patterns_exist(patterns)

    patterns_file = write_patterns_file(patterns, borgmatic_runtime_directory)
    checkpoint_interval = config.get('checkpoint_interval', None)
    checkpoint_volume = config.get('checkpoint_volume', None)
    chunker_params = config.get('chunker_params', None)
    compression = config.get('compression', None)
    upload_rate_limit = config.get('upload_rate_limit', None)
    upload_buffer_size = config.get('upload_buffer_size', None)
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)
    list_filter_flags = make_list_filter_flags(local_borg_version, dry_run)
    files_cache = config.get('files_cache')
    archive_name_format = config.get(
        'archive_name_format', flags.get_default_archive_name_format(local_borg_version)
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
        + make_exclude_flags(config)
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
        + (('--log-json',) if global_arguments.log_json else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (
            ('--list', '--filter', list_filter_flags)
            if list_files and not json and not progress
            else ()
        )
        + (('--dry-run',) if dry_run else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
    )

    create_positional_arguments = flags.make_repository_archive_flags(
        repository_path, archive_name_format, local_borg_version
    )

    # If database hooks are enabled (as indicated by streaming processes), exclude files that might
    # cause Borg to hang. But skip this if the user has explicitly set the "read_special" to True.
    if stream_processes and not config.get('read_special'):
        logger.warning(
            'Ignoring configured "read_special" value of false, as true is needed for database hooks.'
        )
        working_directory = borgmatic.config.paths.get_working_directory(config)

        logger.debug('Collecting special file paths')
        special_file_paths = collect_special_file_paths(
            dry_run,
            create_flags + create_positional_arguments,
            config,
            local_path,
            working_directory,
            borgmatic_runtime_directory=borgmatic_runtime_directory,
        )

        if special_file_paths:
            truncated_special_file_paths = textwrap.shorten(
                ', '.join(special_file_paths),
                width=MAX_SPECIAL_FILE_PATHS_LENGTH,
                placeholder=' ...',
            )
            logger.warning(
                f'Excluding special files to prevent Borg from hanging: {truncated_special_file_paths}'
            )
            patterns_file = write_patterns_file(
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
    local_path='borg',
    remote_path=None,
    progress=False,
    stats=False,
    json=False,
    list_files=False,
    stream_processes=None,
):
    '''
    Given verbosity/dry-run flags, a local or remote repository path, a configuration dict, a
    sequence of loaded configuration paths, the local Borg version, and global arguments as an
    argparse.Namespace instance, create a Borg archive and return Borg's JSON output (if any).

    If a sequence of stream processes is given (instances of subprocess.Popen), then execute the
    create command while also triggering the given processes to produce output.
    '''
    borgmatic.logger.add_custom_log_levels()

    working_directory = borgmatic.config.paths.get_working_directory(config)

    (create_flags, create_positional_arguments, patterns_file) = make_base_create_command(
        dry_run,
        repository_path,
        config,
        patterns,
        local_borg_version,
        global_arguments,
        borgmatic_runtime_directory,
        local_path,
        remote_path,
        progress,
        json,
        list_files,
        stream_processes,
    )

    if json:
        output_log_level = None
    elif list_files or (stats and not dry_run):
        output_log_level = logging.ANSWER
    else:
        output_log_level = logging.INFO

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    output_file = DO_NOT_CAPTURE if progress else None

    create_flags += (
        (('--info',) if logger.getEffectiveLevel() == logging.INFO and not json else ())
        + (('--stats',) if stats and not json and not dry_run else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) and not json else ())
        + (('--progress',) if progress else ())
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
    elif output_log_level is None:
        return execute_command_and_capture_output(
            create_flags + create_positional_arguments,
            working_directory=working_directory,
            environment=environment.make_environment(config),
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
    else:
        execute_command(
            create_flags + create_positional_arguments,
            output_log_level,
            output_file,
            working_directory=working_directory,
            environment=environment.make_environment(config),
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
