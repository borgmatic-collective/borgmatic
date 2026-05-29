import contextlib
import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.archive
import borgmatic.actions.browse.bindings
import borgmatic.actions.browse.icons
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.workers


def get_relative_archive_path_components(archive_path, current_directory_path_components):
    '''
    Given an Archive_path instance and a tuple of path components for the currently browsed
    directory, get the path components as a tuple for the archive path relative to that directory.

    For instance, given an archive path with a path of 'foo/bar/baz/quux.txt' and current
    directory path components of ('foo', 'bar'), return ('baz', 'quux.txt').

    If the archive path is not actually relative to the current directory, return None.
    '''
    archive_path_components = tuple(archive_path.file_path.split(os.path.sep))

    if not current_directory_path_components:
        return archive_path_components

    # If the loaded path doesn't match this directory list's own path, then we don't care about
    # it for purposes of displaying this particular directory.
    if (
        tuple(archive_path_components[: len(current_directory_path_components)])
        != current_directory_path_components
    ):
        return None

    # Strip off the portion of the archive path that matches the directory list's own path.
    return archive_path_components[len(current_directory_path_components) :]


def make_directory_list_option(archive_path, relative_path_components):
    '''
    Given an Archive_path instance and a tuple of relative path components for it, make a
    textual.widgets.option_list.Option for the path. Use an the icon based on whether this looks
    like a terminal filename or a directory.
    '''
    pieces = (
        borgmatic.actions.browse.icons.PATH_TYPE_ICONS.get(
            archive_path.path_type if len(relative_path_components) == 1 else 'd', '❓'
        ),
        relative_path_components[0],
    ) + (('→', archive_path.link_target) if archive_path.link_target else ())

    return textual.widgets.option_list.Option(
        prompt=' '.join(pieces), id=relative_path_components[0]
    )


def add_archive_paths(
    directory_list,
    config,
    repository,
    archive_name,
    archive_paths,
):
    '''
    Given a DirectoryList instance, a configuration dict, a repository dict, an archive name, and a
    sequence of ArchivePath instances, add the paths to the directory list as options, sorting and
    deduplicating the resulting directory list's options.

    After all of this reshuffling, make sure the orignal highlighted option remains highlighted.
    '''
    highlighted_option = directory_list.highlighted_option
    original_options_count = len(directory_list.options)

    sorted_options = sorted(
        (
            *directory_list.options,
            *(
                make_directory_list_option(archive_path, relative_path_components)
                for archive_path in archive_paths
                for relative_path_components in (
                    get_relative_archive_path_components(
                        archive_path,
                        directory_list.path_components,
                    ),
                )
                if relative_path_components
                if not relative_path_components[0] in directory_list._id_to_option
            ),
        ),
        # The loading indicator "option" always goes to the bottom.
        key=lambda option: ((option.id == 'loading-indicator'), option.prompt),
    )

    # If there aren't actually any options to add (due to deduplication), bail.
    if len(sorted_options) == original_options_count:
        return

    # Retain the highlighted option position even as other options load around it.
    directory_list.set_options(sorted_options)
    directory_list.highlighted = (
        directory_list.get_option_index(highlighted_option.id)
        if highlighted_option and directory_list.highlighted_option_changed
        else 0
    )


class Directory_list(textual.widgets.OptionList):
    '''
    A widget for selecting a path from among the contents of a particular directory in a Borg
    archive. The item selection event is handled in a Carousel instance, the parent widget of a
    Directory_list.
    '''

    BINDINGS = borgmatic.actions.browse.bindings.OPTION_LIST_BINDINGS

    def __init__(self, config, repository, archive_name, path_loaded=None, path_components=None):
        '''
        Given a configuration dict, a repository dict, an archive name, an optional
        Archive_path_loaded instance for signalling new paths as they load, and an optional tuple of
        path components indicating this directory's position in the backed up filesystem, start
        loading paths from the archive for eventual display in this widget. Or, if paths have
        already started loading (by the root directory list), just listen for new paths as they come
        in.
        '''
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.path_components = path_components or ()
        self.highlighted_option_changed = False

        super().__init__(classes='panel')

        self.border_title = ' '.join(
            (
                '📁',
                os.path.sep.join(self.path_components)
                if self.path_components
                else f'{archive_name}',
            )
        )

        if self.path_components:
            self.add_option(
                textual.widgets.option_list.Option(
                    '📁 ..',
                    id='..',
                ),
            )

        self.path_loaded = path_loaded or borgmatic.actions.browse.workers.Archive_path_loaded(
            self, 'archive path loaded'
        )

        if not self.path_loaded.complete:
            self.timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

        if not self.path_components:
            borgmatic.actions.browse.workers.load_archive_paths(
                self.app,
                directory_list=self,
                config=self.config,
                repository=self.repository,
                archive_name=self.archive_name,
            )

    def on_mount(self):
        '''
        When this widgets gets mounted in the DOM, subcribe to path loaded events so that we can
        find out about relevant archive paths as they load. And if this is a non-root directory
        list, add any already loaded archive paths to this widget as options. This is done *after*
        subscribing to path loaded signals so that there's not a gap where we might miss out on any
        paths.
        '''
        self.path_loaded.subscribe(self, self.on_archive_path_loaded)

        if self.path_components:
            add_archive_paths(
                directory_list=self,
                config=self.config,
                repository=self.repository,
                archive_name=self.archive_name,
                archive_paths=borgmatic.actions.browse.workers.get_paths(
                    self.path_loaded.path_hierarchy, self.path_components
                ),
            )

    def on_archive_path_loaded(self, data):
        '''
        When an archive path loads, add it as an option to this directory list. But if we get a
        signal that all path loading is complete, stop and remove our loading indicator.
        '''
        if data is borgmatic.actions.browse.workers.LOADING_DONE:
            self.timer.stop()
            self.remove_option('loading-indicator')
            return

        add_archive_paths(
            directory_list=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            archive_paths=(data,),
        )

    def on_option_list_option_highlighted(self, event):
        '''
        When the highlighted option changes, record that fact. This flag is consumed in
        add_archive_paths() in order to retain the highlighted option even as other options load
        around it.
        '''
        if self.highlighted not in {None, 0}:
            self.highlighted_option_changed = True
