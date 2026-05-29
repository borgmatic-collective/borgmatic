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
        Given a configuration dict and a repository dict, start loading the archives from the
        repository for eventual display in this widget.
        '''
        self.config = config
        self.repository = repository

        super().__init__(classes='panel')
        self.border_title = '📚 archives'
        self.highlighted_option_changed = False

        timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

        borgmatic.actions.browse.workers.add_repository_archives(
            self.app,
            archives_list=self,
            config=self.config,
            repository=self.repository,
            timer=timer,
        )

    def on_option_list_option_highlighted(self, event):
        '''
        When the highlighted option changes, record that fact. This flag is consumed in
        borgmatic.actions.browse.workers.add_repository_archives() in order to retain the
        highlighted option even as other options load around it.
        '''
        if self.highlighted not in {None, 0}:
            self.highlighted_option_changed = True
