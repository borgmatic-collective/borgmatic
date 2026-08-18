import os

import textual.widgets

import borgmatic.actions.browse.bindings


class Configuration_files_list(textual.widgets.OptionList):
    '''
    A widget for selecting a single borgmatic configuration file from among available configuration
    files. The item selection event is handled in a Carousel instance, the parent widget of an
    Configuration_files_list.
    '''

    BINDINGS = borgmatic.actions.browse.bindings.OPTION_LIST_BINDINGS

    def __init__(self, configs):
        '''
        Given a dict mapping from configuration path to corresponding configuration dict, add each
        configuration path as an option to this widget.
        '''
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
        self.border_title = '📄 configuration files'
