import glob
import itertools
import logging
import os
import pathlib
import stat
import tempfile

from borgmatic.borg import environment, feature, flags, state
from borgmatic.execute import (
    DO_NOT_CAPTURE,
    execute_command,
    execute_command_and_capture_output,
    execute_command_with_processes,
)

logger = logging.getLogger(__name__)


def expand_directory(directory):
    '''
    Given a directory path, expand any tilde (representing a user's home directory) and any globs
    therein. Return a list of one or more resulting paths.
    '''
    expanded_directory = os.path.expanduser(directory)

    return glob.glob(expanded_directory) or [expanded_directory]


def expand_directories(directories):
    '''
    Given a sequence of directory paths, expand tildes and globs in each one. Return all the
    resulting directories as a single flattened tuple.
    '''
    if directories is None:
        return ()

    return tuple(
        itertools.chain.from_iterable(expand_directory(directory) for directory in directories)
    )


def expand_home_directories(directories):
    '''
    Given a sequence of directory paths, expand tildes in each one. Do not perform any globbing.
    Return the results as a tuple.
    '''
    if directories is None:
        return ()

    return tuple(os.path.expanduser(directory) for directory in directories)


def map_directories_to_devices(directories):
    '''
    Given a sequence of directories, return a map from directory to an identifier for the device on
    which that directory resides or None if the path doesn't exist.

    This is handy for determining whether two different directories are on the same filesystem (have
    the same device identifier).
    '''
    return {
        directory: os.stat(directory).st_dev if os.path.exists(directory) else None
        for directory in directories
    }


def deduplicate_directories(directory_devices, additional_directory_devices):
    '''
    Given a map from directory to the identifier for the device on which that directory resides,
    return the directories as a sorted tuple with all duplicate child directories removed. For
    instance, if paths is ('/foo', '/foo/bar'), return just: ('/foo',)

    The one exception to this rule is if two paths are on different filesystems (devices). In that
    case, they won't get de-duplicated in case they both need to be passed to Borg (e.g. the
    location.one_file_system option is true).

    The idea is that if Borg is given a parent directory, then it doesn't also need to be given
    child directories, because it will naturally spider the contents of the parent directory. And
    there are cases where Borg coming across the same file twice will result in duplicate reads and
    even hangs, e.g. when a database hook is using a named pipe for streaming database dumps to
    Borg.

    If any additional directory devices are given, also deduplicate against them, but don't include
    them in the returned directories.
    '''
    deduplicated = set()
    directories = sorted(directory_devices.keys())
    additional_directories = sorted(additional_directory_devices.keys())
    all_devices = {**directory_devices, **additional_directory_devices}

    for directory in directories:
        deduplicated.add(directory)
        parents = pathlib.PurePath(directory).parents

        # If another directory in the given list (or the additional list) is a parent of current
        # directory (even n levels up) and both are on the same filesystem, then the current
        # directory is a duplicate.
        for other_directory in directories + additional_directories:
            for parent in parents:
                if (
                    pathlib.PurePath(other_directory) == parent
                    and all_devices[directory] is not None
                    and all_devices[other_directory] == all_devices[directory]
                ):
                    if directory in deduplicated:
                        deduplicated.remove(directory)
                    break

    return tuple(sorted(deduplicated))


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


def make_pattern_flags(location_config, pattern_filename=None):
    '''
    Given a location config dict with a potential patterns_from option, and a filename containing
    any additional patterns, return the corresponding Borg flags for those files as a tuple.
    '''
    pattern_filenames = tuple(location_config.get('patterns_from') or ()) + (
        (pattern_filename,) if pattern_filename else ()
    )

    return tuple(
        itertools.chain.from_iterable(
            ('--patterns-from', pattern_filename) for pattern_filename in pattern_filenames
        )
    )


def make_exclude_flags(location_config, exclude_filename=None):
    '''
    Given a location config dict with various exclude options, and a filename containing any exclude
    patterns, return the corresponding Borg flags as a tuple.
    '''
    exclude_filenames = tuple(location_config.get('exclude_from') or ()) + (
        (exclude_filename,) if exclude_filename else ()
    )
    exclude_from_flags = tuple(
        itertools.chain.from_iterable(
            ('--exclude-from', exclude_filename) for exclude_filename in exclude_filenames
        )
    )
    caches_flag = ('--exclude-caches',) if location_config.get('exclude_caches') else ()
    if_present_flags = tuple(
        itertools.chain.from_iterable(
            ('--exclude-if-present', if_present)
            for if_present in location_config.get('exclude_if_present', ())
        )
    )
    keep_exclude_tags_flags = (
        ('--keep-exclude-tags',) if location_config.get('keep_exclude_tags') else ()
    )
    exclude_nodump_flags = ('--exclude-nodump',) if location_config.get('exclude_nodump') else ()

    return (
        exclude_from_flags
        + caches_flag
        + if_present_flags
        + keep_exclude_tags_flags
        + exclude_nodump_flags
    )


DEFAULT_ARCHIVE_NAME_FORMAT = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'


def collect_borgmatic_source_directories(borgmatic_source_directory):
    '''
    Return a list of borgmatic-specific source directories used for state like database backups.
    '''
    if not borgmatic_source_directory:
        borgmatic_source_directory = state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY

    return (
        [borgmatic_source_directory]
        if os.path.exists(os.path.expanduser(borgmatic_source_directory))
        else []
    )


ROOT_PATTERN_PREFIX = 'R '


def pattern_root_directories(patterns=None):
    '''
    Given a sequence of patterns, parse out and return just the root directories.
    '''
    if not patterns:
        return []

    return [
        pattern.split(ROOT_PATTERN_PREFIX, maxsplit=1)[1]
        for pattern in patterns
        if pattern.startswith(ROOT_PATTERN_PREFIX)
    ]


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
    create_command, local_path, working_directory, borg_environment, skip_directories
):
    '''
    Given a Borg create command as a tuple, a local Borg path, a working directory, and a dict of
    environment variables to pass to Borg, and a sequence of parent directories to skip, collect the
    paths for any special files (character devices, block devices, and named pipes / FIFOs) that
    Borg would encounter during a create. These are all paths that could cause Borg to hang if its
    --read-special flag is used.
    '''
    paths_output = execute_command_and_capture_output(
        create_command + ('--dry-run', '--list'),
        capture_stderr=True,
        working_directory=working_directory,
        extra_environment=borg_environment,
    )

    paths = tuple(
        path_line.split(' ', 1)[1]
        for path_line in paths_output.split('\n')
        if path_line and path_line.startswith('- ')
    )

    return tuple(
        path
        for path in paths
        if special_file(path) and not any_parent_directories(path, skip_directories)
    )


def create_archive(
    dry_run,
    repository,
    location_config,
    storage_config,
    local_borg_version,
    local_path='borg',
    remote_path=None,
    progress=False,
    stats=False,
    json=False,
    list_files=False,
    stream_processes=None,
):
    '''
    Given vebosity/dry-run flags, a local or remote repository path, a location config dict, and a
    storage config dict, create a Borg archive and return Borg's JSON output (if any).

    If a sequence of stream processes is given (instances of subprocess.Popen), then execute the
    create command while also triggering the given processes to produce output.
    '''
    borgmatic_source_directories = expand_directories(
        collect_borgmatic_source_directories(location_config.get('borgmatic_source_directory'))
    )
    sources = deduplicate_directories(
        map_directories_to_devices(
            expand_directories(
                tuple(location_config.get('source_directories', ())) + borgmatic_source_directories
            )
        ),
        additional_directory_devices=map_directories_to_devices(
            expand_directories(pattern_root_directories(location_config.get('patterns')))
        ),
    )

    ensure_files_readable(location_config.get('patterns_from'), location_config.get('exclude_from'))

    try:
        working_directory = os.path.expanduser(location_config.get('working_directory'))
    except TypeError:
        working_directory = None

    pattern_file = (
        write_pattern_file(location_config.get('patterns'), sources)
        if location_config.get('patterns') or location_config.get('patterns_from')
        else None
    )
    exclude_file = write_pattern_file(
        expand_home_directories(location_config.get('exclude_patterns'))
    )
    checkpoint_interval = storage_config.get('checkpoint_interval', None)
    chunker_params = storage_config.get('chunker_params', None)
    compression = storage_config.get('compression', None)
    upload_rate_limit = storage_config.get('upload_rate_limit', None)
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)
    files_cache = location_config.get('files_cache')
    archive_name_format = storage_config.get('archive_name_format', DEFAULT_ARCHIVE_NAME_FORMAT)
    extra_borg_options = storage_config.get('extra_borg_options', {}).get('create', '')

    if feature.available(feature.Feature.ATIME, local_borg_version):
        atime_flags = ('--atime',) if location_config.get('atime') is True else ()
    else:
        atime_flags = ('--noatime',) if location_config.get('atime') is False else ()

    if feature.available(feature.Feature.NOFLAGS, local_borg_version):
        noflags_flags = ('--noflags',) if location_config.get('flags') is False else ()
    else:
        noflags_flags = ('--nobsdflags',) if location_config.get('flags') is False else ()

    if feature.available(feature.Feature.NUMERIC_IDS, local_borg_version):
        numeric_ids_flags = ('--numeric-ids',) if location_config.get('numeric_ids') else ()
    else:
        numeric_ids_flags = ('--numeric-owner',) if location_config.get('numeric_ids') else ()

    if feature.available(feature.Feature.UPLOAD_RATELIMIT, local_borg_version):
        upload_ratelimit_flags = (
            ('--upload-ratelimit', str(upload_rate_limit)) if upload_rate_limit else ()
        )
    else:
        upload_ratelimit_flags = (
            ('--remote-ratelimit', str(upload_rate_limit)) if upload_rate_limit else ()
        )

    if stream_processes and location_config.get('read_special') is False:
        logger.warning(
            f'{repository}: Ignoring configured "read_special" value of false, as true is needed for database hooks.'
        )

    create_command = (
        tuple(local_path.split(' '))
        + ('create',)
        + make_pattern_flags(location_config, pattern_file.name if pattern_file else None)
        + make_exclude_flags(location_config, exclude_file.name if exclude_file else None)
        + (('--checkpoint-interval', str(checkpoint_interval)) if checkpoint_interval else ())
        + (('--chunker-params', chunker_params) if chunker_params else ())
        + (('--compression', compression) if compression else ())
        + upload_ratelimit_flags
        + (
            ('--one-file-system',)
            if location_config.get('one_file_system') or stream_processes
            else ()
        )
        + numeric_ids_flags
        + atime_flags
        + (('--noctime',) if location_config.get('ctime') is False else ())
        + (('--nobirthtime',) if location_config.get('birthtime') is False else ())
        + (('--read-special',) if location_config.get('read_special') or stream_processes else ())
        + noflags_flags
        + (('--files-cache', files_cache) if files_cache else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--list', '--filter', 'AMEx-') if list_files and not json and not progress else ())
        + (('--dry-run',) if dry_run else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + flags.make_repository_archive_flags(repository, archive_name_format, local_borg_version)
        + (sources if not pattern_file else ())
    )

    if json:
        output_log_level = None
    elif (stats or list_files) and logger.getEffectiveLevel() == logging.WARNING:
        output_log_level = logging.WARNING
    else:
        output_log_level = logging.INFO

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    output_file = DO_NOT_CAPTURE if progress else None

    borg_environment = environment.make_environment(storage_config)

    # If database hooks are enabled (as indicated by streaming processes), exclude files that might
    # cause Borg to hang. But skip this if the user has explicitly set the "read_special" to True.
    if stream_processes and not location_config.get('read_special'):
        logger.debug(f'{repository}: Collecting special file paths')
        special_file_paths = collect_special_file_paths(
            create_command,
            local_path,
            working_directory,
            borg_environment,
            skip_directories=borgmatic_source_directories,
        )
        logger.warning(
            f'{repository}: Excluding special files to prevent Borg from hanging: {", ".join(special_file_paths)}'
        )

        exclude_file = write_pattern_file(
            expand_home_directories(
                tuple(location_config.get('exclude_patterns') or ()) + special_file_paths
            ),
            pattern_file=exclude_file,
        )

        if exclude_file:
            create_command += make_exclude_flags(location_config, exclude_file.name)

    create_command += (
        (('--info',) if logger.getEffectiveLevel() == logging.INFO and not json else ())
        + (('--stats',) if stats and not json and not dry_run else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) and not json else ())
        + (('--progress',) if progress else ())
        + (('--json',) if json else ())
    )

    if stream_processes:
        return execute_command_with_processes(
            create_command,
            stream_processes,
            output_log_level,
            output_file,
            borg_local_path=local_path,
            working_directory=working_directory,
            extra_environment=borg_environment,
        )
    elif output_log_level is None:
        return execute_command_and_capture_output(
            create_command, working_directory=working_directory, extra_environment=borg_environment,
        )
    else:
        execute_command(
            create_command,
            output_log_level,
            output_file,
            borg_local_path=local_path,
            working_directory=working_directory,
            extra_environment=borg_environment,
        )
