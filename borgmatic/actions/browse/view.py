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
    browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
    browse_app.call_from_thread(timer.stop)

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    for archive in reversed(archives_data['archives']):
        browse_app.call_from_thread(
            archives_list.add_option,
            textual.widgets.option_list.Option(archive['archive'], id=archive['archive']),
        )


@textual.work(thread=True)
def add_archive_files(browse_app, files_list, config, repository, archive_name, timer):
    paths = borgmatic.actions.browse.controller.get_archive_files(config, repository, archive_name)
    browse_app.call_from_thread(timer.stop)
    browse_app.call_from_thread(files_list.remove_option, 'loading-indicator')

    for path in paths:
        browse_app.call_from_thread(
            files_list.add_option,
            textual.widgets.option_list.Option(path, id=path),
        )


class Configuration_files_list(textual.widgets.OptionList):
    def __init__(self, configs):
        self.configs = configs
        home_directory = os.path.expanduser('~')

        super().__init__(
            *(
                textual.widgets.option_list.Option(f'{unexpanded_path}', id=config_path)
                for config_path in configs.keys()
                for unexpanded_path in (config_path.replace(home_directory, '~'),)

            ),
            id='configuration-files-list',
            classes='panel',
        )
        self.border_title = 'configuration files'

    def make_preview(self, option_id):
        return Repositories_list(config=self.configs[option_id])


class Repositories_list(textual.widgets.OptionList):
    def __init__(self, config):
        self.config = config
        self.repositories = config['repositories']

        super().__init__(
            *(
                textual.widgets.option_list.Option(label, id=index)
                for index, repository in enumerate(self.repositories)
                for label in (repository.get('label', repository.get('path')),)
            ),
            id='repositories-list',
            classes='panel',
        )
        self.border_title = 'repositories'

    def make_preview(self, option_id):
        return Archives_list(config=self.config, repository=self.repositories[option_id])


class Archives_list(textual.widgets.OptionList):
    def __init__(self, config, repository):
        self.config = config
        self.repository = repository

        super().__init__(id='archives-list', classes='panel')
        self.border_title = 'archives'

        timer = add_inline_loading_indicator(self)

        add_repository_archives(
            self.app,
            archives_list=self,
            config=self.config,
            repository=self.repository,
            timer=timer,
        )

    def make_preview(self, option_id):
        return Files_list(config=self.config, repository=self.repository, archive_name=option_id)


class Files_list(textual.widgets.OptionList):
    def __init__(self, config, repository, archive_name):
        self.config = config
        self.repository = repository
        self.archive_name = archive_name

        super().__init__(id='files-list', classes='panel')
        self.border_title = 'files'

        timer = add_inline_loading_indicator(self)

        add_archive_files(
            self.app,
            files_list=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            timer=timer,
        )


class Carousel(textual.containers.Horizontal):
    def __init__(self, option_lists):
        self.option_lists = option_lists
        self.focused_option_list = option_lists[0]
        self.preview_option_list = None

        super().__init__()

    def compose(self):
        for option_list in self.option_lists:
            yield option_list

        self.focused_option_list.focus()

    def on_option_list_option_highlighted(self, event):
        if event.option_list != self.focused_option_list:
            return

        # Remove any existing preview from the option list.
        focused_index = self.option_lists.index(event.option_list)
        del(self.option_lists[(focused_index + 1):])

        # Add a fresh preview.
        self.preview_option_list = event.option_list.make_preview(event.option_id)
        self.option_lists.append(self.preview_option_list)
        self.refresh(recompose=True)

    def on_option_list_option_selected(self, event):
        if event.option_list != self.focused_option_list or not self.preview_option_list:
            return

        self.focused_option_list.styles.display = 'none'
        self.focused_option_list = self.preview_option_list
        self.preview_option_list = None

        self.focused_option_list.styles.display = 'block'
        self.focused_option_list.focus()
        self.focused_option_list.highlighted = 0

        # Trigger on_option_list_option_highlighted() for the newly focused option list.
        self.focused_option_list.post_message(
            self.focused_option_list.OptionHighlighted(
                self.focused_option_list,
                self.focused_option_list.options[0],
                0,
            )
        )


class Logs(textual.widgets.RichLog):
    def __init__(self):
        super().__init__(markup=True, classes='panel')
        self.border_title = 'logs'


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

        #logs-container {
            height: 50%;
            display: none;
        }
    '''

    def __init__(self, configs):
        self.configs = configs

        super().__init__()

    def compose(self):
        yield textual.widgets.Header()
        yield Carousel([Configuration_files_list(self.configs)])

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
