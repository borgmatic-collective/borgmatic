import os

import borgmatic.actions.config.bootstrap
import borgmatic.actions.pattern
import borgmatic.borg.check
import borgmatic.borg.create
import borgmatic.borg.environment
import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.pattern
import borgmatic.borg.repo_list
import borgmatic.config.paths
import borgmatic.execute


def collect_and_process_patterns(
    repository, archive, config, local_borg_version, global_arguments, borgmatic_runtime_directory
):
    '''
    Given a repository configuration dict, an archive name, a configuration dict, the local Borg
    version, global arguments as an argparse.Namespace instance, and the borgmatic runtime
    directory, collect, process, and return the configured patterns plus any patterns for bootstrap
    configuration paths.
    '''
    working_directory = borgmatic.config.paths.get_working_directory(config)
    bootstrap_config_paths = borgmatic.actions.config.bootstrap.load_config_paths_from_archive(
        repository['path'],
        archive,
        config,
        local_borg_version,
        global_arguments,
        borgmatic_runtime_directory,
    )

    return borgmatic.actions.pattern.process_patterns(
        borgmatic.actions.pattern.collect_patterns(config, working_directory)
        + tuple(
            borgmatic.borg.pattern.Pattern(
                config_path,
                source=borgmatic.borg.pattern.Pattern_source.INTERNAL,
            )
            for config_path in bootstrap_config_paths
        ),
        config,
        working_directory,
    )


def make_borg_archive_path(path):
    '''
    Given a path, return a copy with any run of leading ".." or "/" path components removed. The
    intent is to mirror what Borg does when storing paths; they're relative to the root of the
    archive, without a leading "/".

    Return "." if no path components remain after the removals.
    '''
    components = path.split(os.path.sep)

    for index, component in enumerate(components):
        if component in {'..', ''}:
            continue

        return os.path.sep.join(components[index:]) or '.'

    return '.'


def make_source_to_archive_root_map(patterns):
    '''
    Given a sequence of processed patterns, return a sequence of tuples mapping from each root
    pattern path (normalized) to that path rewritten in the same way that Borg rewrites paths for
    storing in an archive. This means that slashdot hacks ("/./") are applied, leading slashes are
    removed, etc.

    For example, given the following patterns:

        (
            Pattern('/foo'),
            Pattern('/bar/./baz'),
            Pattern('/bar/baz'),
            Pattern('/bar/baz/quux'),
        )

    ... produces the following return value:

        (
            ('/bar/baz/quux', 'bar/baz/quux'),
            ('/bar/baz', 'bar/baz'),
            ('/bar/baz', 'baz'),
            ('/foo', 'foo'),
        )

    Note how there are edge cases that produce multiple values with the same normalized source path.
    That's why the return value is a sequence of tuples rather than a dict.
    '''
    root_paths = []

    for pattern in patterns:
        if pattern.type != borgmatic.borg.pattern.Pattern_type.ROOT:
            continue

        slashdot_position = pattern.path.find('/./')
        normalized_source_path = os.path.normpath(pattern.path)

        # If there's no slashdot hack in the path, just use the normalized path.
        if slashdot_position <= 0:
            root_paths.append(
                (normalized_source_path, make_borg_archive_path(normalized_source_path))
            )

            continue

        strip_prefix = os.path.normpath(pattern.path[:slashdot_position]) + os.path.sep

        # If basically the entire path gets stripped off, that just leaves "." to store in the
        # archive. This can happen due to normalization, e.g. when the pattern path is something
        # like "/foo/./bar/..".
        if normalized_source_path + os.path.sep == strip_prefix:
            root_paths.append((normalized_source_path, '.'))

            continue

        if normalized_source_path.startswith(strip_prefix):
            root_paths.append(
                (
                    normalized_source_path,
                    make_borg_archive_path(normalized_source_path.removeprefix(strip_prefix)),
                )
            )

            continue

        # After normalization, the slashdot isn't there anymore. There must have been a subsequent
        # ".." that removed it. Example: "/foo/./..".
        root_paths.append(
            (normalized_source_path, make_borg_archive_path(normalized_source_path) or '.')
        )

    # Sort by longest source paths first, as they're the most specific matches. This is important
    # for edge cases where there are two source paths referring to the same file, but Borg only
    # stores one of them (e.g. due to the "one_file_system" option excluding it).
    return tuple(sorted(root_paths, key=lambda paths: len(paths[0]), reverse=True))


def replace_root_path_prefix(source_path, source_root_path, archive_root_path):
    '''
    Return a copy of the given source path, modified to replace the given source root prefix with
    the given archive root prefix.
    '''
    return make_borg_archive_path(
        os.path.normpath(
            archive_root_path
            if source_path == source_root_path
            else os.path.join(
                archive_root_path,
                source_path.removeprefix(source_root_path + os.path.sep),
            )
        )
    )


def map_source_path_to_archive_path(source_path, archive_paths, source_to_archive_root_paths):
    '''
    Given a normalized source path, a set of Borg paths actually found in the archive, and a
    sequence of tuples mapping from normalized source root paths to archive root paths, return the
    given normalized source path rewritten as a Borg archive path. This means replacing the source
    root prefix in the normalized source path with the corresponding archive root prefix, preferring
    the longest candidate path that actually exists in the given archive paths (falling back to the
    longest candidate). If there's no such source root prefix, then just return the source path with
    any leading run of "/" and ".." stripped.
    '''
    candidate_archive_paths = (
        archive_path
        for source_root_path, archive_root_path in source_to_archive_root_paths
        # We only care about root paths that actually prefix this source path.
        if source_path.startswith(source_root_path + os.path.sep) or source_path == source_root_path
        for archive_path in (
            replace_root_path_prefix(source_path, source_root_path, archive_root_path),
        )
    )

    try:
        return next(
            iter(
                sorted(
                    candidate_archive_paths,
                    # Prefer archive paths that are actually in the archive. (False sorts before
                    # True, hence the "not".)
                    key=lambda archive_path: not bool(archive_path in archive_paths),
                )
            )
        )
    except StopIteration:
        return make_borg_archive_path(source_path)
