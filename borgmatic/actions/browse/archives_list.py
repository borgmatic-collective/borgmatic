import contextlib
import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.bindings
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.workers


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
            loading_timer=self.loading_timer,
        )

    def on_archive_loaded(self, archive_name):
        '''
        When an archive loads, add it as an option to this archives list. But if we get a
        signal that all path loading is complete, stop and remove our loading indicator.
        '''
        if archive_name is borgmatic.actions.browse.workers.LOADING_DONE:
            self.loading_timer.stop()
            self.remove_option('loading-indicator')
            return

        label_pieces = (
            (archive_name, '[dim](latest)[/dim]') if len(self.options) == 1 else (archive_name,)
        )
        highlighted_option = self.highlighted_option

        loading_indicator = self.get_option('loading-indicator')
        self.remove_option('loading-indicator')
        self.add_options(
            (
                textual.widgets.option_list.Option(' '.join(label_pieces), id=archive_name),
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
