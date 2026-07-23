import logging
import os

import textual
import textual.signal

import borgmatic.actions.browse.archive

logger = logging.getLogger('__name__')


LOADING_DONE = object()


class Archive_loaded(textual.signal.Signal):
    '''
    A signal that publishes when each subsequent archive is loaded from a repository, intended for
    consumption in widgets that display archives as they are loaded. This signal also publishes
    when loading is complete.

    Each subscribed callback call includes the archive as an archive name string. Given the lack of
    other identifying information (configuration file, repository), there should be a separate
    Archive_loaded instance per repository.
    '''


@textual.work(thread=True)
def add_repository_archives(browse_app, archive_loaded, config, repository):
    '''
    Given a running Browse_app instance, an Archive_loaded instance, a configuration dict, and a
    repository dict, load a list of the archives from the repository and add them as options in the
    archives list. Reverse the order so the most recent archive is first.

    This function runs in a separate thread from the main UI. When loading is complete, publish a
    loading done signal.
    '''
    archives_data = borgmatic.actions.browse.archive.get_repository_archives(config, repository)

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    for archive in reversed(archives_data['archives']):
        archive_loaded.publish(archive['archive'])

    archive_loaded.publish(LOADING_DONE)


def record_path(archive_path, hierarchy, path_components):
    '''
    Given an Archive_path instance, a dict capturing a filesystem hierarchy of paths, and a tuple of
    path components for the archive path, set the archive path into the hierarchy data structure.

    For instance, if given an archive path and path components representing "foo/bar/baz.txt",
    produce a hierarchy that looks like:

        {'foo': {'bar': {'baz.txt': Archive_path('-', 'foo/bar/baz.txt', '')}}}

    Note that the hierarchy is modified in place, so any existing paths there are retained.
    '''
    if len(path_components) == 1:
        hierarchy[path_components[0]] = {} if archive_path.path_type == 'd' else archive_path
        return

    record_path(archive_path, hierarchy.setdefault(path_components[0], {}), path_components[1:])


def get_paths(hierarchy, path_components, full_path_components=None):
    '''
    Given a dict capturing a filesystem hierarchy of paths (or a subset thereof), a tuple of path
    components for a directory path relative to the hierarchy root, and an optional tuple of
    *absolute* path components for the same path (if different), return a generator of the
    contained file and directory Archive_path instances from the hierarchy.

    For instance, given the following hierarchy:

        {'foo': {'bar': {'baz.txt': Archive_path('-', 'foo/bar/baz.txt', ''), 'quux': {}}}}

    ... and path components of ('foo', 'bar'), return a generator with the following:

        * Archive_path('-', 'foo/bar/baz.txt', '')
        * Archive_path('d', 'foo/bar/quux', '')

    The given absolute path components are use to construct directory paths like that last archive
    path.
    '''
    if full_path_components is None:
        full_path_components = path_components

    if len(path_components) == 1:
        try:
            return (
                archive_path
                if isinstance(archive_path, borgmatic.actions.browse.archive.Archive_path)
                else borgmatic.actions.browse.archive.Archive_path(
                    'd', os.path.join(*full_path_components, component), ''
                )
                for component, archive_path in hierarchy[path_components[0]].items()
            )
        except KeyError:
            raise ValueError(f'Unknown file or directory: {path_components[0]}')

    try:
        return get_paths(hierarchy[path_components[0]], path_components[1:], full_path_components)
    except KeyError:
        raise ValueError(f'Unknown directory: {path_components[0]}')


class Archive_path_loaded(textual.signal.Signal):
    '''
    A signal that publishes when each subsequent path is loaded from an archive, intended for
    consumption in widgets that display paths as they are loaded. This signal also tracks the
    complete filesystem hierarchy seen thus far, so new widgets that get created after loading has
    started can "catch up" with existing known paths. Lastly, this signal publishes and tracks when
    loading is complete.

    Each subscrided callback call includes the loaded path as an Archive_path instance. There is
    intended to be a separate Archive_path_loaded instance per archive, but that instance should be
    shared among several different widgets for the same archive for performance reasons.
    '''

    def __init__(self, owner, name):
        self.path_hierarchy = {}
        self.complete = False

        super().__init__(owner, name)

    def publish(self, archive_path):
        '''
        Publish the given archive path to subscribers and record its path locally. But if the
        archive path is actually LOADING_DONE, then record loading as complete.
        '''
        super().publish(archive_path)

        if archive_path is LOADING_DONE:
            self.complete = True
        else:
            record_path(
                archive_path, self.path_hierarchy, archive_path.file_path.split(os.path.sep)
            )


@textual.work(thread=True)
def load_archive_paths(browse_app, path_loaded, config, repository, archive_name):
    '''
    Given a running Browse_app instance, an Archive_path_loaded instance, a configuration dict, a
    repository dict, and an archive name, load the paths in this archive and publish each one via
    the Archive_path_loaded signal, so interested widgets can subscribe. Also send a "loading done"
    signal when loading completes.

    This function runs in a separate thread from the main UI. When loading is complete, publish a
    loading done signal.
    '''
    for archive_path in borgmatic.actions.browse.archive.get_archive_paths(
        config, repository, archive_name
    ):
        path_loaded.publish(archive_path)

    path_loaded.publish(LOADING_DONE)


class File_preview_loaded(textual.signal.Signal):
    '''
    A signal that publishes when file contents are loaded from an archive, intended for consumption
    in widgets that display loaded files. This signal also publishes when loading is complete.

    Each published callback includes a the file's contents as a string. Given the lack of other
    identifying information (configuration file, repository, archive), there should be a separate
    Archive_loaded instance per previewed file.
    '''


@textual.work(thread=True)
def load_file_preview(
    browse_app,
    file_preview_loaded,
    config,
    repository,
    archive_name,
    file_path,
):
    '''
    Given a running Browse_app instance, a File_preview_loaded instance, a configuration dict, a
    repository dict, an archive name, and the path of a file in that archive, load the contents of
    the file and write it into the given file preview widget.

    This function runs in a separate thread from the main UI. When loading is complete, publish a
    loading done signal.
    '''
    file_contents = borgmatic.actions.browse.archive.get_archive_file_content(
        config, repository, archive_name, file_path
    )

    file_preview_loaded.publish(file_contents)
