import contextlib
import enum
import functools
import os
import logging

import borgmatic.actions.browse.controller

import rich.text
import textual._context
import textual.app
import textual.color
import textual.binding
import textual.reactive
import textual.widgets


class Path_type(enum.Enum):
    DIRECTORY = 3
    FILE = 4
    DUMP = 5
    BOOTSTRAP = 6
    LOADING = 7


PATH_TYPE_ICONS = {
    Path_type.DIRECTORY: '📁',
    Path_type.FILE: '📄',
    Path_type.DUMP: '🗄️',
    Path_type.BOOTSTRAP: '🥾',
}
PATH_TYPE_EXPANDED_ICONS = {Path_type.DIRECTORY: '📂'}
LOADING_DOT_INTERVAL_SECONDS = 0.3


def update_inline_loading_indicator(option_list, loading_option):
    option_list.replace_option_prompt(
        'loading-indicator', (str(loading_option.prompt) + '.').replace('....', '')
    )


def add_inline_loading_indicator(option_list):
    option_list.clear_options()
    loading_option = textual.widgets.option_list.Option(f'⏳ Loading...', id='loading-indicator')
    option_list.add_option(loading_option)

    return option_list.set_interval(
        LOADING_DOT_INTERVAL_SECONDS,
        functools.partial(update_inline_loading_indicator, option_list, loading_option),
    )


@textual.work(thread=True)
async def add_repository_archives(
    browse_app, archives_list, config, repository, timer
):
    archives_data = borgmatic.actions.browse.controller.get_repository_archives(config, repository)

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    browse_app.call_from_thread(
        archives_list.add_options,
        (
            textual.widgets.option_list.Option(archive['archive'], id=archive['archive'])
            for archive in reversed(archives_data['archives'])
        ),
    )

    browse_app.call_from_thread(timer.stop)
    browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')


# FIXME: Revamp for option list instead of tree.
@textual.work(thread=True)
def add_archive_files(browse_tree, archive_node, config, repository, archive, timer, loading_node):
    files_data = borgmatic.actions.browse.controller.get_archive_files(config, repository, archive)
    config = archive_node.data['config']
    repository = archive_node.data['repository']
    archive = archive_node.data['archive']

    for file_data in files_data:
        add_path(
            browse_tree, archive_node, config, repository, archive, timer, loading_node, file_data
        )

    browse_tree.app.call_from_thread(loading_node.remove)
    browse_tree.app.call_from_thread(timer.stop)


class Configuration_files_list(textual.widgets.OptionList):
    def __init__(self, configs):
        super().__init__(
            *(
                textual.widgets.option_list.Option(f'{config_path}', id=config_path)
                for config_path in configs.keys()
            ),
            id='configuration-files-list',
            classes='panel',
        )
        self.configs = configs
        self.border_title = 'configuration files'


class Repositories_list(textual.widgets.OptionList):
    def __init__(self):
        super().__init__(id='repositories-list', classes='panel')
        self.border_title = 'repositories'

    def set_repositories(self, config):
        self.config = config
        self.repositories = config['repositories']

        self.clear_options()
        self.add_options(
            textual.widgets.option_list.Option(label, id=index)
            for index, repository in enumerate(self.repositories)
            for label in (repository.get('label', repository.get('path')),)
        )


class Archives_list(textual.widgets.OptionList):
    def __init__(self):
        super().__init__(id='archives-list', classes='panel')
        self.border_title = 'archives'


class Logs(textual.widgets.RichLog):
    def __init__(self):
        super().__init__(markup=True, classes='panel')
        self.border_title = 'logs'


def unexpand_path(config_path):
    home_directory = os.path.expanduser('~')

    if config_path.startswith(home_directory):
        return config_path.replace(home_directory, '~')

    return config_path


class Browse_app(textual.app.App):
    BINDINGS = [
        textual.binding.Binding(key='q', action='quit', description='quit'),
        textual.binding.Binding(key='l', action='toggle_logs', description='logs'),
        textual.binding.Binding(
            key='c', action='command_palette', description='commands', show=False
        ),
    ]
    COMMAND_PALETTE_BINDING = 'c'
    CSS = '''
        .panel {
            border: round $primary;
            border-title-color: $text-primary;
            height: 100%;
        }

        #archives-list {
            display: none;
        }

        #logs-container {
            height: 50%;
            display: none;
        }
    '''

    def __init__(self, configs):
        self.configs = configs

        super().__init__()

    def compose(self):
        self.configuration_files_list = Configuration_files_list(self.configs)
        self.repositories_list = Repositories_list()
        self.archives_list = Archives_list()

        yield textual.widgets.Header()
        with textual.containers.Horizontal():
            yield self.configuration_files_list
            yield self.repositories_list
            yield self.archives_list

        with textual.containers.Horizontal(id='logs-container'):
            logs_widget = Logs()
            yield logs_widget
        yield textual.widgets.Footer()

        handler = Browse_log_handler(self, logs_widget)
        handler.setFormatter(Rich_color_formatter())
        logger = logging.getLogger()
        logger.setLevel(min(handler.level for handler in logger.handlers))
        logger.addHandler(handler)

        # Remove the console log handler so it doesn't try to log all over our UI; we have our own
        # log handler for surfacing logs within the UI.
        with contextlib.suppress(StopIteration):
            console_handler = next(
                handler
                for handler in logging.getLogger().handlers
                if isinstance(handler, borgmatic.logger.Multi_stream_handler)
            )
            logger.removeHandler(console_handler)

    def on_mount(self):
        self.title = 'borgmatic browse'

    def on_option_list_option_highlighted(self, event):
        if event.option_list == self.configuration_files_list:
            config = self.configuration_files_list.configs[event.option_id]
            self.repositories_list.set_repositories(config)
        elif event.option_list == self.repositories_list:
            timer = add_inline_loading_indicator(self.archives_list)

            add_repository_archives(
                self,
                archives_list=self.archives_list,
                config=self.repositories_list.config,
                repository=self.repositories_list.repositories[event.option_id],
                timer=timer,
            )

    def on_option_list_option_selected(self, event):
        if event.option_list == self.configuration_files_list:
            self.configuration_files_list.styles.display = 'none'
            self.archives_list.styles.display = 'block'
            self.repositories_list.focus()
            self.repositories_list.highlighted = 0

    def action_toggle_logs(self):
        logs_container = self.query_one('#logs-container')
        logs_container.styles.display = (
            'none' if logs_container.styles.display == 'block' else 'block'
        )


class Browse_log_handler(logging.Handler):
    def __init__(self, app, logs_widget):
        self.app = app
        self.logs_widget = logs_widget

        super().__init__()

    def emit(self, record):
        message = self.format(record)

        try:
            worker = textual.worker.get_current_worker()
            self.app.call_from_thread(self.logs_widget.write, message)
        except (RuntimeError, textual.worker.NoActiveWorker):
            with contextlib.suppress(textual._context.NoActiveAppError):
                self.logs_widget.write(message)


class Rich_color_formatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.prefix = None
        super().__init__(
            '{prefix}{message}',
            *args,
            style='{',
            **kwargs,
        )

    def format(self, record):
        borgmatic.logger.add_custom_log_levels()

        color = {
            logging.CRITICAL: 'bright_red',
            logging.ERROR: 'bright_red',
            logging.WARNING: 'bright_yellow',
            logging.ANSWER: 'bright_magenta',
            logging.INFO: 'bright_green',
            logging.DEBUG: 'bright_cyan',
        }.get(record.levelno)
        record.prefix = f'{self.prefix}: ' if self.prefix else ''

        return f'[{color}]{super().format(record)}[/{color}]'


def run_browse(
    diff_arguments,
    global_arguments,
    configs,
):
    '''
    Run the "browse" action for the given repository.
    '''
    if not configs:
        return

    logging.getLogger('asyncio').setLevel(logging.WARNING)

    app = Browse_app(configs)
    app.run()
