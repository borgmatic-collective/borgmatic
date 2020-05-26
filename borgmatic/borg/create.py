import glob
import itertools
import logging
import os
import pathlib
import tempfile

from borgmatic.execute import DO_NOT_CAPTURE, execute_command, execute_command_with_processes

logger = logging.getLogger(__name__)


def _expand_directory(directory):
    '''
    Given a directory path, expand any tilde (representing a user's home directory) and any globs
    therein. Return a list of one or more resulting paths.
    '''
    expanded_directory = os.path.expanduser(directory)

    return glob.glob(expanded_directory) or [expanded_directory]


def _expand_directories(directories):
    '''
    Given a sequence of directory paths, expand tildes and globs in each one. Return all the
    resulting directories as a single flattened tuple.
    '''
    if directories is None:
        return ()

    return tuple(
        itertools.chain.from_iterable(_expand_directory(directory) for directory in directories)
    )


def _expand_home_directories(directories):
    '''
    Given a sequence of directory paths, expand tildes in each one. Do not perform any globbing.
    Return the results as a tuple.
    '''
    if directories is None:
        return ()

    return tuple(os.path.expanduser(directory) for directory in directories)


def deduplicate_directories(directories):
    '''
    Given a sequence of directories, return them as a sorted tuple with all duplicate child
    directories removed. For instance, if paths is ('/foo', '/foo/bar'), return just: ('/foo',)

    The idea is that if Borg is given a parent directory, then it doesn't also need to be given
    child directories, because it will naturally spider the contents of the parent directory. And
    there are cases where Borg coming across the same file twice will result in duplicate reads and
    even hangs, e.g. when a database hook is using a named pipe for streaming database dumps to
    Borg.
    '''
    deduplicated = set()

    for directory in sorted(directories):
        # If the directory is "/", that contains all child directories, so we can early out.
        if directory == os.path.sep:
            return (os.path.sep,)

        # If no other directories are parents of current directory (even n levels up), then the
        # current directory isn't a duplicate.
        if not any(
            pathlib.PurePath(other_directory) in pathlib.PurePath(directory).parents
            for other_directory in directories
        ):
            deduplicated.add(directory)

    return tuple(sorted(deduplicated))


def _write_pattern_file(patterns=None):
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


def _make_pattern_flags(location_config, pattern_filename=None):
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


def _make_exclude_flags(location_config, exclude_filename=None):
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
        _expand_directories(
            location_config['source_directories']
            + borgmatic_source_directories(location_config.get('borgmatic_source_directory'))
        )
    )

    pattern_file = _write_pattern_file(location_config.get('patterns'))
    exclude_file = _write_pattern_file(
        _expand_home_directories(location_config.get('exclude_patterns'))
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

    full_command = (
        (local_path, 'create')
        + _make_pattern_flags(location_config, pattern_file.name if pattern_file else None)
        + _make_exclude_flags(location_config, exclude_file.name if exclude_file else None)
        + (('--checkpoint-interval', str(checkpoint_interval)) if checkpoint_interval else ())
        + (('--chunker-params', chunker_params) if chunker_params else ())
        + (('--compression', compression) if compression else ())
        + (('--remote-ratelimit', str(remote_rate_limit)) if remote_rate_limit else ())
        + (
            ('--one-file-system',)
            if location_config.get('one_file_system') or stream_processes
            else ()
        )
        + (('--numeric-owner',) if location_config.get('numeric_owner') else ())
        + (('--noatime',) if location_config.get('atime') is False else ())
        + (('--noctime',) if location_config.get('ctime') is False else ())
        + (('--nobirthtime',) if location_config.get('birthtime') is False else ())
        + (('--read-special',) if (location_config.get('read_special') or stream_processes) else ())
        + (('--nobsdflags',) if location_config.get('bsd_flags') is False else ())
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
        )

    return execute_command(full_command, output_log_level, output_file, borg_local_path=local_path)
