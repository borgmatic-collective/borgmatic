import contextlib
import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.bindings
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.workers


class Configuration_files_list(textual.widgets.OptionList):
    BINDINGS = borgmatic.actions.browse.bindings.OPTION_LIST_BINDINGS

    def __init__(self, configs):
        self.configs = configs
        home_directory = os.path.expanduser('~')

        super().__init__(
            *(
                textual.widgets.option_list.Option(unexpanded_path, id=config_path)
                for config_path in configs
                for unexpanded_path in (config_path.replace(home_directory, '~'),)
            ),
            classes='panel',
        )
        self.border_title = 'configuration files'
