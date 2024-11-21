import itertools
import logging
import os
import pathlib
import stat
import tempfile
import textwrap

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


def expand_home_directories(directories):
    '''
    Given a sequence of directory paths, expand tildes in each one. Do not perform any globbing.
    Return the results as a tuple.
    '''
    if directories is None:
        return ()

    return tuple(os.path.expanduser(directory) for directory in directories)


def write_pattern_file(patterns=None, sources=None, pattern_file=None):
    '''
    Given a sequence of patterns and an optional sequence of source directories, write them to a
    named temporary file (with the source directories as additional roots) and return the file.
    If an optional open pattern file is given, overwrite it instead of making a new temporary file.
    Return None if no patterns are provided.
    '''
    if not patterns and not sources:
        return None

    if pattern_file is None:
        pattern_file = tempfile.NamedTemporaryFile('w')
    else:
        pattern_file.seek(0)

    pattern_file.write(
        '\n'.join(tuple(patterns or ()) + tuple(f'R {source}' for source in (sources or [])))
    )
    pattern_file.flush()

    return pattern_file


def ensure_files_readable(*filename_lists):
    '''
    Given a sequence of filename sequences, ensure that each filename is openable. This prevents
    unreadable files from being passed to Borg, which in certain situations only warns instead of
    erroring.
    '''
    for file_object in itertools.chain.from_iterable(
        filename_list for filename_list in filename_lists if filename_list
    ):
        open(file_object).close()


def make_pattern_flags(config, pattern_filename=None):
    '''
    Given a configuration dict with a potential patterns_from option, and a filename containing any
    additional patterns, return the corresponding Borg flags for those files as a tuple.
    '''
    pattern_filenames = tuple(config.get('patterns_from') or ()) + (
        (pattern_filename,) if pattern_filename else ()
    )

    return tuple(
        itertools.chain.from_iterable(
            ('--patterns-from', pattern_filename) for pattern_filename in pattern_filenames
        )
    )


def make_exclude_flags(config, exclude_filename=None):
    '''
    Given a configuration dict with various exclude options, and a filename containing any exclude
    patterns, return the corresponding Borg flags as a tuple.
    '''
    exclude_filenames = tuple(config.get('exclude_from') or ()) + (
        (exclude_filename,) if exclude_filename else ()
    )
    exclude_from_flags = tuple(
        itertools.chain.from_iterable(
            ('--exclude-from', exclude_filename) for exclude_filename in exclude_filenames
        )
    )
    caches_flag = ('--exclude-caches',) if config.get('exclude_caches') else ()
    if_present_flags = tuple(
        itertools.chain.from_iterable(
            ('--exclude-if-present', if_present)
            for if_present in config.get('exclude_if_present', ())
        )
    )
    keep_exclude_tags_flags = ('--keep-exclude-tags',) if config.get('keep_exclude_tags') else ()
    exclude_nodump_flags = ('--exclude-nodump',) if config.get('exclude_nodump') else ()

    return (
        exclude_from_flags
        + caches_flag
        + if_present_flags
        + keep_exclude_tags_flags
        + exclude_nodump_flags
    )


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


ROOT_PATTERN_PREFIX = 'R '


def special_file(path):
    '''
    Return whether the given path is a special file (character device, block device, or named pipe
    / FIFO).
    '''
    try:
        mode = os.stat(path).st_mode
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
    create_command, config, local_path, working_directory, borg_environment, skip_directories
):
    '''
    Given a Borg create command as a tuple, a configuration dict, a local Borg path, a working
    directory, a dict of environment variables to pass to Borg, and a sequence of parent directories
    to skip, collect the paths for any special files (character devices, block devices, and named
    pipes / FIFOs) that Borg would encounter during a create. These are all paths that could cause
    Borg to hang if its --read-special flag is used.
    '''
    # Omit "--exclude-nodump" from the Borg dry run command, because that flag causes Borg to open
    # files including any named pipe we've created.
    paths_output = execute_command_and_capture_output(
        tuple(argument for argument in create_command if argument != '--exclude-nodump')
        + ('--dry-run', '--list'),
        capture_stderr=True,
        working_directory=working_directory,
        extra_environment=borg_environment,
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )

    paths = tuple(
        path_line.split(' ', 1)[1]
        for path_line in paths_output.split('\n')
        if path_line and path_line.startswith('- ') or path_line.startswith('+ ')
    )

    return tuple(
        path
        for path in paths
        if special_file(path) and not any_parent_directories(path, skip_directories)
    )


def check_all_source_directories_exist(source_directories, working_directory=None):
    '''
    Given a sequence of source directories and an optional working directory to serve as a prefix
    for each (if it's a relative directory), check that the source directories all exist. If any do
    not, raise an exception.
    '''
    missing_directories = [
        source_directory
        for source_directory in source_directories
        if not all(
            [
                os.path.exists(os.path.join(working_directory or '', directory))
                for directory in expand_directory(source_directory, working_directory)
            ]
        )
    ]
    if missing_directories:
        raise ValueError(f"Source directories do not exist: {', '.join(missing_directories)}")


MAX_SPECIAL_FILE_PATHS_LENGTH = 1000


def make_base_create_command(
    dry_run,
    repository_path,
    config,
    config_paths,
    source_directories,
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
    Given vebosity/dry-run flags, a local or remote repository path, a configuration dict, a
    sequence of loaded configuration paths, the local Borg version, global arguments as an
    argparse.Namespace instance, and a sequence of borgmatic source directories, return a tuple of
    (base Borg create command flags, Borg create command positional arguments, open pattern file
    handle, open exclude file handle).
    '''
    working_directory = borgmatic.config.paths.get_working_directory(config)

    if config.get('source_directories_must_exist', False):
        check_all_source_directories_exist(
            config.get('source_directories'), working_directory=working_directory
        )

    ensure_files_readable(config.get('patterns_from'), config.get('exclude_from'))

    pattern_file = (
        write_pattern_file(config.get('patterns'), source_directories)
        if config.get('patterns') or config.get('patterns_from')
        else None
    )
    exclude_file = write_pattern_file(expand_home_directories(config.get('exclude_patterns')))
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
        + make_pattern_flags(config, pattern_file.name if pattern_file else None)
        + make_exclude_flags(config, exclude_file.name if exclude_file else None)
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
    ) + (tuple(source_directories) if not pattern_file else ())

    # If database hooks are enabled (as indicated by streaming processes), exclude files that might
    # cause Borg to hang. But skip this if the user has explicitly set the "read_special" to True.
    if stream_processes and not config.get('read_special'):
        logger.warning(
            f'{repository_path}: Ignoring configured "read_special" value of false, as true is needed for database hooks.'
        )
        borg_environment = environment.make_environment(config)

        logger.debug(f'{repository_path}: Collecting special file paths')
        special_file_paths = collect_special_file_paths(
            create_flags + create_positional_arguments,
            config,
            local_path,
            working_directory,
            borg_environment,
            skip_directories=(
                [borgmatic_runtime_directory] if os.path.exists(borgmatic_runtime_directory) else []
            ),
        )

        if special_file_paths:
            truncated_special_file_paths = textwrap.shorten(
                ', '.join(special_file_paths),
                width=MAX_SPECIAL_FILE_PATHS_LENGTH,
                placeholder=' ...',
            )
            logger.warning(
                f'{repository_path}: Excluding special files to prevent Borg from hanging: {truncated_special_file_paths}'
            )
            exclude_file = write_pattern_file(
                expand_home_directories(
                    tuple(config.get('exclude_patterns') or ()) + special_file_paths
                ),
                pattern_file=exclude_file,
            )
            create_flags += make_exclude_flags(config, exclude_file.name)

    return (create_flags, create_positional_arguments, pattern_file, exclude_file)


def create_archive(
    dry_run,
    repository_path,
    config,
    config_paths,
    source_directories,
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
    Given vebosity/dry-run flags, a local or remote repository path, a configuration dict, a
    sequence of loaded configuration paths, the local Borg version, and global arguments as an
    argparse.Namespace instance, create a Borg archive and return Borg's JSON output (if any).

    If a sequence of stream processes is given (instances of subprocess.Popen), then execute the
    create command while also triggering the given processes to produce output.
    '''
    borgmatic.logger.add_custom_log_levels()

    working_directory = borgmatic.config.paths.get_working_directory(config)

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        make_base_create_command(
            dry_run,
            repository_path,
            config,
            config_paths,
            source_directories,
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

    borg_environment = environment.make_environment(config)

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
            extra_environment=borg_environment,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
    elif output_log_level is None:
        return execute_command_and_capture_output(
            create_flags + create_positional_arguments,
            working_directory=working_directory,
            extra_environment=borg_environment,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
    else:
        execute_command(
            create_flags + create_positional_arguments,
            output_log_level,
            output_file,
            working_directory=working_directory,
            extra_environment=borg_environment,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
