import textual.app
import textual.binding
import textual.widgets

import borgmatic.actions.browse.logs
import borgmatic.actions.browse.widgets


class Browse_app(textual.app.App):
    BINDINGS = [
        textual.binding.Binding(key='q', action='quit', description='quit'),
        textual.binding.Binding(key='v', action='toggle_logs', description='view logs'),
        textual.binding.Binding(
            key='c', action='command_palette', description='commands', show=False
        ),
    ]
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
        yield textual.widgets.Header()
        yield borgmatic.actions.browse.widgets.Carousel(
            [borgmatic.actions.browse.widgets.Configuration_files_list(self.configs)]
            if len(self.configs) > 1
            else [
                borgmatic.actions.browse.widgets.Repositories_list(tuple(self.configs.values())[0])
            ]
        )

        logs_widget = borgmatic.actions.browse.widgets.Logs()
        yield logs_widget
        yield textual.widgets.Footer()

        borgmatic.actions.browse.logs.log_to_widget(logs_widget)

    def on_mount(self):
        self.title = 'borgmatic browse'

    def action_toggle_logs(self):
        logs_container = self.query_one('#logs')
        logs_container.styles.display = (
            'none' if logs_container.styles.display == 'block' else 'block'
        )
