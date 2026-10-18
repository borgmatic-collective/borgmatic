import os

import rich.text
import textual.widgets

import borgmatic.actions.browse.archive
import borgmatic.actions.browse.bindings
import borgmatic.actions.browse.icons
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.sizes
import borgmatic.actions.browse.workers

OPTION_SIZE_COLUMN_WIDTH = 10


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


def make_size_path_prompt(size, path_text):
    '''
    Given a size in bytes (or None for a path that has no size), and plain text for a path, return a
    Rich renderable of the size right-justified in a fixed-width column with the path beside it, so
    that the paths in a list of options all line up, the way they do in ncdu or ls -l.

    A rich.text.Text rather than a rich.table.Table, even though a table is the more natural fit for
    columns. Textual measures the height of every option whenever it rebuilds its line cache, and
    replacing any option's prompt does exactly that. Measuring a table lays out its columns from
    scratch, which made rebuilding the line cache for 2,000 options about 45x slower than measuring
    text—dwarfing the cost of actually painting the options. Should more columns arrive, that cost
    may be worth paying, but it isn't for one.
    '''
    size_text = borgmatic.actions.browse.sizes.format_size(size) if size is not None else ''

    return rich.text.Text(f'{size_text:>{OPTION_SIZE_COLUMN_WIDTH}}  {path_text}')


def make_directory_list_option(archive_path, relative_path_components, size):
    '''
    Given an Archive_path instance, a tuple of relative path components for it, and a size in bytes
    for the path, make a textual.widgets.option_list.Option for the path. Use an the icon based on
    whether this looks like a terminal filename or a directory, and show a human-readable size in a
    column beside it.

    Only show a link target for an archive path that is actually this option. For a nested path, the
    option is the directory containing the path, so it has no link target of its own.

    Since the option's prompt is a Rich renderable rather than a string, also stash plain text for
    the same information on the option as prompt_text, plus its path type as path_type. That way,
    consumers like the sort in add_archive_paths() or the next panel lookup in the carousel don't
    have to see through the renderable.
    '''
    is_leaf = len(relative_path_components) == 1
    path_type = (
        archive_path.path_type
        if is_leaf
        else borgmatic.actions.browse.archive.Path_type.DIRECTORY.value
    )
    pieces = (
        borgmatic.actions.browse.icons.PATH_TYPE_ICONS.get(path_type, '❓'),
        relative_path_components[0],
    ) + (('→', archive_path.link_target) if is_leaf and archive_path.link_target else ())

    option = textual.widgets.option_list.Option(
        prompt=make_size_path_prompt(size, ' '.join(pieces)),
        id=relative_path_components[0],
    )
    option.prompt_text = ' '.join(
        (*pieces, f'({borgmatic.actions.browse.sizes.format_size(size)})')
    )
    option.path_type = path_type

    return option


def get_prompt_text(option):
    '''
    Given a textual.widgets.option_list.Option, return the plain text equivalent of its prompt.
    Directory list options prompt with a Rich renderable and stash the plain text as prompt_text,
    while other options (e.g. the loading indicator) prompt with an ordinary string.
    '''
    return getattr(option, 'prompt_text', None) or str(option.prompt)


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
    deduplicating the resulting directory list's options. For paths that already have options,
    instead update their displayed sizes, since directory sizes grow as more archive paths load.

    First collapse the paths to a single representative per displayed option, since a batch usually
    contains many paths beneath the same directory and each directory's size only needs computing
    once.

    After all of this reshuffling, make sure the original highlighted option remains highlighted.
    '''
    # Textual 6.0.0+ has self.highlighted_option for this, but we want to support older versions.
    highlighted_option = (
        directory_list.options[directory_list.highlighted]
        if directory_list.highlighted is not None
        else None
    )
    new_options = []

    # Index the options already displayed, so that we can update them in place below.
    existing_options = {option.id: option for option in directory_list.options}

    # Keep just one path per option. Prefer a direct child of this directory over a nested path,
    # since the direct child is what defines the option's own type and link target.
    representatives = {}

    for archive_path in archive_paths:
        relative_path_components = get_relative_archive_path_components(
            archive_path, directory_list.path_components
        )

        # If the loaded path doesn't belong to this directory list, we don't care about it.
        if not relative_path_components:
            continue

        option_id = relative_path_components[0]

        if option_id not in representatives or len(relative_path_components) == 1:
            representatives[option_id] = (archive_path, relative_path_components)

    for option_id, (archive_path, relative_path_components) in representatives.items():
        # A directory's cumulative size lives in the hierarchy rather than in the archive listing,
        # which reports directories themselves as zero-sized.
        size = (
            borgmatic.actions.browse.workers.get_path_size(
                directory_list.path_loaded.path_hierarchy,
                (*directory_list.path_components, option_id),
            )
            if len(relative_path_components) > 1
            or archive_path.path_type == borgmatic.actions.browse.archive.Path_type.DIRECTORY.value
            else archive_path.size
        )
        option = make_directory_list_option(archive_path, relative_path_components, size)
        existing_option = existing_options.get(option_id)

        if existing_option is None:
            new_options.append(option)
        elif get_prompt_text(existing_option) != option.prompt_text:
            directory_list.replace_option_prompt(option_id, option.prompt)

            # Keep the existing option's plain text and path type in sync with its replaced
            # renderable, so that the check above still suppresses no-op repaints below.
            existing_option.prompt_text = option.prompt_text
            existing_option.path_type = option.path_type

    # If there aren't actually any new options to add, we're done after the size updates above.
    if not new_options:
        return

    sorted_options = sorted(
        (*directory_list.options, *new_options),
        # The loading indicator "option" always goes to the bottom.
        key=lambda option: ((option.id == 'loading-indicator'), get_prompt_text(option)),
    )

    # Retain the highlighted option position even as other options load around it.
    directory_list.clear_options()
    directory_list.add_options(sorted_options)
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
        path components indicating this directory's position in the backed up filesystem, prepare to
        load paths from the archive for eventual display in this widget. Actual loading kicks off in
        on_mount() below.
        '''
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.path_components = path_components or ()
        self.highlighted_option_changed = False

        super().__init__(classes='panel')

        if self.path_components:
            # Lay ".." out like the other options, even though it has no size of its own.
            parent_option = textual.widgets.option_list.Option(
                prompt=make_size_path_prompt(None, '📁 ..'),
                id='..',
            )
            parent_option.prompt_text = '📁 ..'
            self.add_option(parent_option)

        self.path_loaded = path_loaded or borgmatic.actions.browse.workers.Archive_path_loaded(
            self, 'archive path loaded'
        )

        self.update_border_title()

        if not self.path_loaded.complete:
            self.timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

    def on_mount(self):
        '''
        When this widget gets mounted in the DOM, subscribe to path loaded events so that we can
        find out about relevant archive paths as they load. And if this is a root directory list,
        start loading paths from the archive. If this is a non-root directory list, add any already
        loaded archive paths to this widget as options.

        Loading is started *after* subscribing to path loaded signals so that there's not a gap
        where we might miss out on any paths.
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
        else:
            borgmatic.actions.browse.workers.load_archive_paths(
                self.app,
                path_loaded=self.path_loaded,
                config=self.config,
                repository=self.repository,
                archive_name=self.archive_name,
            )

        self.update_border_title()

    def update_border_title(self):
        '''
        Update this directory list's border title with the cumulative size of the directory it
        displays (or the entire archive, for a root directory list). Skip the update if the title
        hasn't actually changed, since refreshing the border on every loaded path flickers.
        '''
        size = borgmatic.actions.browse.workers.get_path_size(
            self.path_loaded.path_hierarchy, self.path_components
        )
        title = ' '.join(
            (
                '📁',
                os.path.sep.join(self.path_components)
                if self.path_components
                else f'{self.archive_name}',
                f'({borgmatic.actions.browse.sizes.format_size(size)})',
            )
        )

        if title != self.border_title:
            self.border_title = title

    def on_archive_path_loaded(self, data):
        '''
        When a batch of archive paths loads, add them as options to this directory list. But if we
        get a signal that all path loading is complete, stop and remove our loading indicator.
        '''
        if data is borgmatic.actions.browse.workers.LOADING_DONE:
            self.timer.stop()
            self.remove_option('loading-indicator')
            self.update_border_title()
            return

        add_archive_paths(
            directory_list=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            archive_paths=data,
        )

        self.update_border_title()

    def on_option_list_option_highlighted(self, event):
        '''
        When the highlighted option changes, record that fact. This flag is consumed in
        add_archive_paths() in order to retain the highlighted option even as other options load
        around it.
        '''
        if self.highlighted not in {None, 0}:
            self.highlighted_option_changed = True
