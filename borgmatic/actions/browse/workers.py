import contextlib
import logging
import os

import rich.syntax
import textual
import textual.signal
import textual.widgets.option_list

import borgmatic.actions.browse.archive


logger = logging.getLogger('__name__')


@textual.work(thread=True)
def add_repository_archives(browse_app, archives_list, config, repository, loading_timer):
    '''
    Given a running Browse_app instance, an Archives_list instance, a configuration dict, a
    repository dict, and a loading indicator timer, load a list of the archives from the repository
    and add them as options in the archives list. Reverse the order so the most recent archive is
    first.

    This function runs in a separate thread from the main UI. When loading is complete, remove the
    loading indicator and stop its timer.
    '''
    archives_data = borgmatic.actions.browse.archive.get_repository_archives(config, repository)
    loading_option = archives_list.get_option('loading-indicator')

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    for index, archive in enumerate(reversed(archives_data['archives'])):
        label_pieces = (
            (archive['archive'], '[dim](latest)[/dim]') if index == 0 else (archive['archive'],)
        )
        highlighted_option = archives_list.highlighted_option

        browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
        browse_app.call_from_thread(
            archives_list.add_options,
            (
                textual.widgets.option_list.Option(' '.join(label_pieces), id=archive['archive']),
                loading_option,
            ),
        )

        # Retain the highlighted option position even as other options load around it.
        archives_list.highlighted = (
            archives_list.get_option_index(highlighted_option.id)
            if highlighted_option and archives_list.highlighted_option_changed
            else 0
        )

    browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
    browse_app.call_from_thread(loading_timer.stop)


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
    components for an archive path relative to the hierarchy root, and an optional tuple of
    *absolute* path components for the same archive path (if different), return the corresponding
    Archive_path from the hierarchy.

    For instance, given the following hierarchy:

        {'foo': {'bar': {'baz.txt': Archive_path('-', 'foo/bar/baz.txt', '')}}}

    ... and path components of ('foo', 'bar', 'baz.txt'), return the Archive_path instance above.

    Or in the case of path components of only ('foo', 'bar'), return a directory with the absolute
    path:

        Archive_path('d', 'foo/bar', '')
    '''
    if full_path_components is None:
        full_path_components = path_components

    if len(path_components) == 1:
        return (
            archive_path
            if isinstance(archive_path, borgmatic.actions.browse.archive.Archive_path)
            else borgmatic.actions.browse.archive.Archive_path(
                'd', os.path.join(*full_path_components, component), ''
            )
            for component, archive_path in hierarchy[path_components[0]].items()
        )

    return get_paths(hierarchy[path_components[0]], path_components[1:], full_path_components)


LOADING_DONE = object()


class Archive_path_loaded(textual.signal.Signal):
    '''
    A signal that publishes when each subsequent path is loaded from an archive, intended for
    consumption in widgets that display paths as they are loaded. This signal also tracks the
    complete filesystem hierarchy seen thus far, so new widgets that get created after loading has
    started can "catch up" with existing known paths. Lastly, this signal publishes and tracks when
    loading is complete.
    '''
    def __init__(self, owner, name):
        self.path_hierarchy = {}
        self.complete = False

        super().__init__(owner, name)

    def publish(self, data):
        super().publish(data)

        if data is LOADING_DONE:
            self.complete = True
        else:
            record_path(data, self.path_hierarchy, data.file_path.split(os.path.sep))


@textual.work(thread=True)
def load_archive_paths(browse_app, directory_list, config, repository, archive_name):
    '''
    Given a running Browse_app instance, a Directory_list instance, a configuration dict, a
    repository dict, and an archive name, load the paths in this archive and publish each one via
    the Archive_path_loaded signal, so interested widgets can subscribe. Also send a "loading done"
    signal when loading completes.

    This function runs in a separate thread from the main UI.
    '''
    for archive_path in borgmatic.actions.browse.archive.get_archive_paths(
        config, repository, archive_name
    ):
        directory_list.path_loaded.publish(archive_path)

    directory_list.path_loaded.publish(LOADING_DONE)


@textual.work(thread=True)
def load_file_preview(browse_app, file_preview, config, repository, archive_name, file_path,
                      loading_timer):
    '''
    Given a running Browse_app instance, a File_preview instance, a configuration dict, a repository
    dict, an archive name, the path of a file in that archive, and a loading indicator timer, load
    the contents of the file and write it into the given file preview widget.
    '''
    file_content = borgmatic.actions.browse.archive.get_archive_file_content(
        config, repository, archive_name, file_path
    )

    browse_app.call_from_thread(loading_timer.stop)
    browse_app.call_from_thread(file_preview.clear)

    if file_content is None:
        browse_app.call_from_thread(file_preview.write, 'Cannot display a preview for this file')
    else:
        syntax_lexer = rich.syntax.Syntax.guess_lexer(file_path, file_content)
        browse_app.call_from_thread(
            file_preview.write, rich.syntax.Syntax(file_content, syntax_lexer)
        )
