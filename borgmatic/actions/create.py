import glob
import itertools
import logging
import os
import pathlib

import borgmatic.actions.json
import borgmatic.borg.create
import borgmatic.borg.pattern
import borgmatic.config.paths
import borgmatic.config.validate
import borgmatic.hooks.command
import borgmatic.hooks.dispatch

logger = logging.getLogger(__name__)


def parse_pattern(pattern_line, default_style=borgmatic.borg.pattern.Pattern_style.NONE):
    '''
    Given a Borg pattern as a string, parse it into a borgmatic.borg.pattern.Pattern instance and
    return it.
    '''
    try:
        (pattern_type, remainder) = pattern_line.split(' ', maxsplit=1)
    except ValueError:
        raise ValueError(f'Invalid pattern: {pattern_line}')

    try:
        (parsed_pattern_style, path) = remainder.split(':', maxsplit=1)
        pattern_style = borgmatic.borg.pattern.Pattern_style(parsed_pattern_style)
    except ValueError:
        pattern_style = default_style
        path = remainder

    return borgmatic.borg.pattern.Pattern(
        path,
        borgmatic.borg.pattern.Pattern_type(pattern_type),
        borgmatic.borg.pattern.Pattern_style(pattern_style),
        source=borgmatic.borg.pattern.Pattern_source.CONFIG,
    )


def collect_patterns(config):
    '''
    Given a configuration dict, produce a single sequence of patterns comprised of the configured
    source directories, patterns, excludes, pattern files, and exclude files.

    The idea is that Borg has all these different ways of specifying includes, excludes, source
    directories, etc., but we'd like to collapse them all down to one common format (patterns) for
    ease of manipulation within borgmatic.
    '''
    try:
        return (
            tuple(
                borgmatic.borg.pattern.Pattern(
                    source_directory, source=borgmatic.borg.pattern.Pattern_source.CONFIG
                )
                for source_directory in config.get('source_directories', ())
            )
            + tuple(
                parse_pattern(pattern_line.strip())
                for pattern_line in config.get('patterns', ())
                if not pattern_line.lstrip().startswith('#')
                if pattern_line.strip()
            )
            + tuple(
                parse_pattern(
                    f'{borgmatic.borg.pattern.Pattern_type.NO_RECURSE.value} {exclude_line.strip()}',
                    borgmatic.borg.pattern.Pattern_style.FNMATCH,
                )
                for exclude_line in config.get('exclude_patterns', ())
            )
            + tuple(
                parse_pattern(pattern_line.strip())
                for filename in config.get('patterns_from', ())
                for pattern_line in open(filename).readlines()
                if not pattern_line.lstrip().startswith('#')
                if pattern_line.strip()
            )
            + tuple(
                parse_pattern(
                    f'{borgmatic.borg.pattern.Pattern_type.NO_RECURSE.value} {exclude_line.strip()}',
                    borgmatic.borg.pattern.Pattern_style.FNMATCH,
                )
                for filename in config.get('exclude_from', ())
                for exclude_line in open(filename).readlines()
                if not exclude_line.lstrip().startswith('#')
                if exclude_line.strip()
            )
        )
    except (FileNotFoundError, OSError) as error:
        logger.debug(error)

        raise ValueError(f'Cannot read patterns_from/exclude_from file: {error.filename}')


def expand_directory(directory, working_directory):
    '''
    Given a directory path, expand any tilde (representing a user's home directory) and any globs
    therein. Return a list of one or more resulting paths.

    Take into account the given working directory so that relative paths are supported.
    '''
    expanded_directory = os.path.expanduser(directory)

    # This would be a lot easier to do with glob(..., root_dir=working_directory), but root_dir is
    # only available in Python 3.10+.
    normalized_directory = os.path.join(working_directory or '', expanded_directory)
    glob_paths = glob.glob(normalized_directory)

    if not glob_paths:
        return [expanded_directory]

    working_directory_prefix = os.path.join(working_directory or '', '')

    return [
        (
            glob_path
            # If these are equal, that means we didn't add any working directory prefix above.
            if normalized_directory == expanded_directory
            # Remove the working directory prefix that we added above in order to make glob() work.
            # We can't use os.path.relpath() here because it collapses any use of Borg's slashdot
            # hack.
            else glob_path.removeprefix(working_directory_prefix)
        )
        for glob_path in glob_paths
    ]


def expand_patterns(patterns, working_directory=None, skip_paths=None):
    '''
    Given a sequence of borgmatic.borg.pattern.Pattern instances and an optional working directory,
    expand tildes and globs in each root pattern. Return all the resulting patterns (not just the
    root patterns) as a tuple.

    If a set of paths are given to skip, then don't expand any patterns matching them.
    '''
    if patterns is None:
        return ()

    return tuple(
        itertools.chain.from_iterable(
            (
                (
                    borgmatic.borg.pattern.Pattern(
                        expanded_path,
                        pattern.type,
                        pattern.style,
                        pattern.device,
                        pattern.source,
                    )
                    for expanded_path in expand_directory(pattern.path, working_directory)
                )
                if pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
                and pattern.path not in (skip_paths or ())
                else (pattern,)
            )
            for pattern in patterns
        )
    )


def device_map_patterns(patterns, working_directory=None):
    '''
    Given a sequence of borgmatic.borg.pattern.Pattern instances and an optional working directory,
    determine the identifier for the device on which the pattern's path resides—or None if the path
    doesn't exist or is from a non-root pattern. Return an updated sequence of patterns with the
    device field populated. But if the device field is already set, don't bother setting it again.

    This is handy for determining whether two different pattern paths are on the same filesystem
    (have the same device identifier).
    '''
    return tuple(
        borgmatic.borg.pattern.Pattern(
            pattern.path,
            pattern.type,
            pattern.style,
            device=pattern.device
            or (
                os.stat(full_path).st_dev
                if pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
                and os.path.exists(full_path)
                else None
            ),
            source=pattern.source,
        )
        for pattern in patterns
        for full_path in (os.path.join(working_directory or '', pattern.path),)
    )


def deduplicate_patterns(patterns):
    '''
    Given a sequence of borgmatic.borg.pattern.Pattern instances, return them with all duplicate
    root child patterns removed. For instance, if two root patterns are given with paths "/foo" and
    "/foo/bar", return just the one with "/foo". Non-root patterns are passed through without
    modification.

    The one exception to deduplication is two paths are on different filesystems (devices). In that
    case, they won't get deduplicated, in case they both need to be passed to Borg (e.g. the
    one_file_system option is true).

    The idea is that if Borg is given a root parent pattern, then it doesn't also need to be given
    child patterns, because it will naturally spider the contents of the parent pattern's path. And
    there are cases where Borg coming across the same file twice will result in duplicate reads and
    even hangs, e.g. when a database hook is using a named pipe for streaming database dumps to
    Borg.
    '''
    deduplicated = {}  # Use just the keys as an ordered set.

    for pattern in patterns:
        if pattern.type != borgmatic.borg.pattern.Pattern_type.ROOT:
            deduplicated[pattern] = True
            continue

        parents = pathlib.PurePath(pattern.path).parents

        # If another directory in the given list is a parent of current directory (even n levels up)
        # and both are on the same filesystem, then the current directory is a duplicate.
        for other_pattern in patterns:
            if other_pattern.type != borgmatic.borg.pattern.Pattern_type.ROOT:
                continue

            if any(
                pathlib.PurePath(other_pattern.path) == parent
                and pattern.device is not None
                and other_pattern.device == pattern.device
                for parent in parents
            ):
                break
        else:
            deduplicated[pattern] = True

    return tuple(deduplicated.keys())


def process_patterns(patterns, working_directory, skip_expand_paths=None):
    '''
    Given a sequence of Borg patterns and a configured working directory, expand and deduplicate any
    "root" patterns, returning the resulting root and non-root patterns as a list.

    If any paths are given to skip, don't expand them.
    '''
    skip_paths = set(skip_expand_paths or ())

    return list(
        deduplicate_patterns(
            device_map_patterns(
                expand_patterns(
                    patterns,
                    working_directory=working_directory,
                    skip_paths=skip_paths,
                )
            )
        )
    )


def run_create(
    config_filename,
    repository,
    config,
    config_paths,
    hook_context,
    local_borg_version,
    create_arguments,
    global_arguments,
    dry_run_label,
    local_path,
    remote_path,
):
    '''
    Run the "create" action for the given repository.

    If create_arguments.json is True, yield the JSON output from creating the archive.
    '''
    if create_arguments.repository and not borgmatic.config.validate.repositories_match(
        repository, create_arguments.repository
    ):
        return

    borgmatic.hooks.command.execute_hook(
        config.get('before_backup'),
        config.get('umask'),
        config_filename,
        'pre-backup',
        global_arguments.dry_run,
        **hook_context,
    )

    logger.info(f'Creating archive{dry_run_label}')
    working_directory = borgmatic.config.paths.get_working_directory(config)

    with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )
        patterns = process_patterns(collect_patterns(config), working_directory)
        active_dumps = borgmatic.hooks.dispatch.call_hooks(
            'dump_data_sources',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            config_paths,
            borgmatic_runtime_directory,
            patterns,
            global_arguments.dry_run,
        )

        # Process the patterns again in case any data source hooks updated them. Without this step,
        # we could end up with duplicate paths that cause Borg to hang when it tries to read from
        # the same named pipe twice.
        patterns = process_patterns(patterns, working_directory, skip_expand_paths=config_paths)
        stream_processes = [process for processes in active_dumps.values() for process in processes]

        json_output = borgmatic.borg.create.create_archive(
            global_arguments.dry_run,
            repository['path'],
            config,
            patterns,
            local_borg_version,
            global_arguments,
            borgmatic_runtime_directory,
            local_path=local_path,
            remote_path=remote_path,
            progress=create_arguments.progress,
            stats=create_arguments.stats,
            json=create_arguments.json,
            list_files=create_arguments.list_files,
            stream_processes=stream_processes,
        )

        if json_output:
            yield borgmatic.actions.json.parse_json(json_output, repository.get('label'))

        borgmatic.hooks.dispatch.call_hooks_even_if_unconfigured(
            'remove_data_source_dumps',
            config,
            borgmatic.hooks.dispatch.Hook_type.DATA_SOURCE,
            borgmatic_runtime_directory,
            global_arguments.dry_run,
        )

    borgmatic.hooks.command.execute_hook(
        config.get('after_backup'),
        config.get('umask'),
        config_filename,
        'post-backup',
        global_arguments.dry_run,
        **hook_context,
    )
