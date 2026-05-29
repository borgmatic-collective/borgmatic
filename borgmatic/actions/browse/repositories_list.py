import contextlib
import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.bindings
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.workers


class Repositories_list(textual.widgets.OptionList):
    '''
    A widget for selecting a single Borg repository from among the repositories in a borgmatic
    configuratin file. The item selection event is handled in a Carousel instance, the parent widget
    of a Repositories_list.
    '''

    BINDINGS = borgmatic.actions.browse.bindings.OPTION_LIST_BINDINGS

    def __init__(self, config):
        '''
        Given a configuration dict, populate the repositories in this widget.
        '''
        self.config = config
        self.repositories = config['repositories']

        super().__init__(
            *(
                textual.widgets.option_list.Option(label, id=index)
                for index, repository in enumerate(self.repositories)
                for label in (repository.get('label', repository.get('path')),)
            ),
            classes='panel',
        )
        self.border_title = '📦 repositories'
