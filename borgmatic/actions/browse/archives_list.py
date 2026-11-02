import textual.widgets

import borgmatic.actions.browse.bindings
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.workers


def make_archives_list_option(archive, latest=False):
    '''
    Given an archive dict with "archive" and "id" keys, make a textual.widgets.option_list.Option
    for the archive. Include a "latest" archive indicator in the prompt if latest is True.

    Return the resulting option.
    '''
    prompt_pieces = (archive['archive'], '[dim](latest)[/dim]') if latest else (archive['archive'],)
    option = textual.widgets.option_list.Option(' '.join(prompt_pieces), id=archive['id'])

    # Tack on the unadulterated prompt text, making it easy to get when this option is selected.
    option.prompt_text = archive['archive']

    return option


class Archives_list(textual.widgets.OptionList):
    '''
    A widget for selecting a single Borg archive from among the archives in a repository. The item
    selection event is handled in a Carousel instance, the parent widget of an Archives_list.
    '''

    BINDINGS = borgmatic.actions.browse.bindings.OPTION_LIST_BINDINGS

    def __init__(self, config, repository):
        '''
        Given a configuration dict and a repository dict, prepare to load the archives from the
        repository for eventual display in this widget. Actual loading kicks off in on_mount()
        below.
        '''
        self.config = config
        self.repository = repository

        super().__init__(classes='panel')
        self.border_title = '📚 archives'
        self.highlighted_option_changed = False
        self.archive_loaded = borgmatic.actions.browse.workers.Archive_loaded(
            self, 'archive loaded'
        )

        self.loading_timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

    def on_mount(self):
        '''
        When this widget gets mounted in the DOM, subscribe to archive loaded events so that we can
        find out about archives as they load. Also start loading archives from the repository.

        Loading is started *after* subscribing to the archive loaded signal so that there's not a
        gap where we might miss out on signal publishes.
        '''
        self.archive_loaded.subscribe(self, self.on_archive_loaded)

        borgmatic.actions.browse.workers.add_repository_archives(
            self.app,
            archive_loaded=self.archive_loaded,
            config=self.config,
            repository=self.repository,
        )

    def on_archive_loaded(self, archive):
        '''
        When an archive loads, add it as an option to this archives list. But if we get a
        signal that all path loading is complete, stop and remove our loading indicator.
        '''
        if archive is borgmatic.actions.browse.workers.LOADING_DONE:
            self.loading_timer.stop()
            self.remove_option('loading-indicator')
            return

        # Textual 6.0.0+ has self.highlighted_option, but we want to support older versions.
        highlighted_option = (
            self.options[self.highlighted] if self.highlighted is not None else None
        )

        loading_indicator = self.get_option('loading-indicator')
        self.remove_option('loading-indicator')
        self.add_options(
            (
                make_archives_list_option(archive, latest=bool(len(self.options) == 0)),
                loading_indicator,
            ),
        )

        # Retain the highlighted option position even as other options load around it.
        self.highlighted = (
            self.get_option_index(highlighted_option.id)
            if highlighted_option and self.highlighted_option_changed
            else 0
        )

    def on_option_list_option_highlighted(self, event):
        '''
        When the highlighted option changes, record that fact. This flag is consumed in
        borgmatic.actions.browse.workers.add_repository_archives() in order to retain the
        highlighted option even as other options load around it.
        '''
        if self.highlighted not in {None, 0}:
            self.highlighted_option_changed = True
