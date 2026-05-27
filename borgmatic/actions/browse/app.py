import signal

import textual.app
import textual.binding
import textual.widgets

import borgmatic.actions.browse.carousel
import borgmatic.actions.browse.logs


class Browse_app(textual.app.App):
    '''
    The main app / entry point for the browse action UI.
    '''

    BINDINGS = (
        textual.binding.Binding(key='q', action='quit', description='quit'),
        textual.binding.Binding(key='v', action='toggle_logs', description='view logs'),
        textual.binding.Binding(
            key='c', action='command_palette', description='commands', show=False
        ),
    )
    COMMAND_PALETTE_BINDING = 'c'
    CSS = '''
        .panel {
            border: round $primary;
            border-title-color: $text-primary;
            width: 100%;
            height: 100%;
        }

        #logs {
            width: 100%;
            height: 50%;
            display: none;
        }
    '''

    def __init__(self, configs):
        self.configs = configs

        super().__init__()

    def compose(self):
        '''
        Compose a UI consisting of:

          * a header with the application name
          * a carousel container that contains the main UI panels
          * a logs panel where Python logs show up (panel hidden by default)
          * a footer with available keys listed
        '''
        yield textual.widgets.Header()
        yield borgmatic.actions.browse.carousel.Carousel(
            [borgmatic.actions.browse.panels.Configuration_files_list(self.configs)]
            if len(self.configs) > 1
            else [
                borgmatic.actions.browse.panels.Repositories_list(next(iter(self.configs.values())))
            ]
        )

        logs_panel = borgmatic.actions.browse.panels.Logs()
        yield logs_panel
        yield textual.widgets.Footer()

        borgmatic.actions.browse.logs.log_to_widget(logs_panel)

    def on_mount(self):
        '''
        Set the application title, which ends up in the header.
        '''
        self.title = 'borgmatic browse'

    def action_toggle_logs(self):
        '''
        Toggle the show/hide status of the logs panel.
        '''
        logs_panel = self.query_one('#logs')
        logs_panel.styles.display = 'none' if logs_panel.styles.display == 'block' else 'block'

    def exit(self):  # pragma: no cover
        '''
        Exit the application. But first raise a SIGTERM (handled in borgmatic/signals.py) to
        encourage a fast exit by killing any ongoing Borg subprocesses.
        '''
        signal.raise_signal(signal.SIGTERM)

        super().exit()
