import glob
import itertools
import logging
import os
import pathlib
import tempfile

from borgmatic.borg import feature
from borgmatic.execute import DO_NOT_CAPTURE, execute_command, execute_command_with_processes

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


def deduplicate_directories(directory_devices):
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
    '''
    deduplicated = set()
    directories = sorted(directory_devices.keys())

    for directory in directories:
        deduplicated.add(directory)
        parents = pathlib.PurePath(directory).parents

        # If another directory in the given list is a parent of current directory (even n levels
        # up) and both are on the same filesystem, then the current directory is a duplicate.
        for other_directory in directories:
            for parent in parents:
                if (
                    pathlib.PurePath(other_directory) == parent
                    and directory_devices[directory] is not None
                    and directory_devices[other_directory] == directory_devices[directory]
                ):
                    if directory in deduplicated:
                        deduplicated.remove(directory)
                    break

    return tuple(sorted(deduplicated))


def write_pattern_file(patterns=None):
    '''
    Given a sequence of patterns, write them to a named temporary file and return it. Return None
    if no patterns are provided.
    '''
    if not patterns:
        return None

    pattern_file = tempfile.NamedTemporaryFile('w')
    pattern_file.write('\n'.join(patterns))
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


DEFAULT_BORGMATIC_SOURCE_DIRECTORY = '~/.borgmatic'


def borgmatic_source_directories(borgmatic_source_directory):
    '''
    Return a list of borgmatic-specific source directories used for state like database backups.
    '''
    if not borgmatic_source_directory:
        borgmatic_source_directory = DEFAULT_BORGMATIC_SOURCE_DIRECTORY

    return (
        [borgmatic_source_directory]
        if os.path.exists(os.path.expanduser(borgmatic_source_directory))
        else []
    )


DEFAULT_ARCHIVE_NAME_FORMAT = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'


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
    files=False,
    stream_processes=None,
):
    '''
    Given vebosity/dry-run flags, a local or remote repository path, a location config dict, and a
    storage config dict, create a Borg archive and return Borg's JSON output (if any).

    If a sequence of stream processes is given (instances of subprocess.Popen), then execute the
    create command while also triggering the given processes to produce output.
    '''
    sources = deduplicate_directories(
        map_directories_to_devices(
            expand_directories(
                location_config['source_directories']
                + borgmatic_source_directories(location_config.get('borgmatic_source_directory'))
            )
        )
    )

    try:
        working_directory = os.path.expanduser(location_config.get('working_directory'))
    except TypeError:
        working_directory = None
    pattern_file = write_pattern_file(location_config.get('patterns'))
    exclude_file = write_pattern_file(
        expand_home_directories(location_config.get('exclude_patterns'))
    )
    checkpoint_interval = storage_config.get('checkpoint_interval', None)
    chunker_params = storage_config.get('chunker_params', None)
    compression = storage_config.get('compression', None)
    remote_rate_limit = storage_config.get('remote_rate_limit', None)
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
        noflags_flags = ('--noflags',) if location_config.get('bsd_flags') is False else ()
    else:
        noflags_flags = ('--nobsdflags',) if location_config.get('bsd_flags') is False else ()

    if feature.available(feature.Feature.NUMERIC_IDS, local_borg_version):
        numeric_ids_flags = ('--numeric-ids',) if location_config.get('numeric_owner') else ()
    else:
        numeric_ids_flags = ('--numeric-owner',) if location_config.get('numeric_owner') else ()

    if feature.available(feature.Feature.UPLOAD_RATELIMIT, local_borg_version):
        upload_ratelimit_flags = (
            ('--upload-ratelimit', str(remote_rate_limit)) if remote_rate_limit else ()
        )
    else:
        upload_ratelimit_flags = (
            ('--remote-ratelimit', str(remote_rate_limit)) if remote_rate_limit else ()
        )

    ensure_files_readable(location_config.get('patterns_from'), location_config.get('exclude_from'))

    full_command = (
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
        + (('--read-special',) if (location_config.get('read_special') or stream_processes) else ())
        + noflags_flags
        + (('--files-cache', files_cache) if files_cache else ())
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--list', '--filter', 'AME-') if files and not json and not progress else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO and not json else ())
        + (('--stats',) if stats and not json and not dry_run else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) and not json else ())
        + (('--dry-run',) if dry_run else ())
        + (('--progress',) if progress else ())
        + (('--json',) if json else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + (
            '{repository}::{archive_name_format}'.format(
                repository=repository, archive_name_format=archive_name_format
            ),
        )
        + sources
    )

    if json:
        output_log_level = None
    elif (stats or files) and logger.getEffectiveLevel() == logging.WARNING:
        output_log_level = logging.WARNING
    else:
        output_log_level = logging.INFO

    # The progress output isn't compatible with captured and logged output, as progress messes with
    # the terminal directly.
    output_file = DO_NOT_CAPTURE if progress else None

    if stream_processes:
        return execute_command_with_processes(
            full_command,
            stream_processes,
            output_log_level,
            output_file,
            borg_local_path=local_path,
            working_directory=working_directory,
        )

    return execute_command(
        full_command,
        output_log_level,
        output_file,
        borg_local_path=local_path,
        working_directory=working_directory,
    )
