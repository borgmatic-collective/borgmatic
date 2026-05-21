import contextlib
import enum
import functools
import os
import logging

import borgmatic.actions.browse.controller

import rich.syntax
import rich.text
import textual._context
import textual.app
import textual.color
import textual.binding
import textual.reactive
import textual.widgets


class Path_type(enum.Enum):
    DIRECTORY = 'd'
    LINK = 'l'
    FILE = '-'


PATH_TYPE_ICONS = {
    Path_type.DIRECTORY.value: '📁',
    Path_type.LINK.value: '🔗',
    Path_type.FILE.value: '📄',
}
LOADING_DOT_INTERVAL_SECONDS = 0.3


logger = logging.getLogger('__name__')


def update_inline_loading_indicator(widget):
    if isinstance(widget, textual.widgets.OptionList):
        try:
            widget.replace_option_prompt(
                'loading-indicator', (str(widget.get_option('loading-indicator').prompt) + '.').replace('....', '')
            )
        except textual.widgets.option_list.OptionDoesNotExist:
            pass
    elif isinstance(widget, textual.widgets.Static):
        widget.update((str(widget.content) + '.').replace('....', ''))
    else:
        raise ValueError(f'Unsupported widget type: {type(widget)}')


def add_inline_loading_indicator(widget):
    loading_message = f'⏳ loading...'

    if isinstance(widget, textual.widgets.OptionList):
        widget.clear_options()
        loading_option = textual.widgets.option_list.Option(loading_message, id='loading-indicator')
        widget.add_option(loading_option)
        widget.highlighted = None
    elif isinstance(widget, textual.widgets.Static):
        widget.update(loading_message)
    else:
        raise ValueError(f'Unsupported widget type: {type(widget)}')

    return widget.set_interval(
        LOADING_DOT_INTERVAL_SECONDS,
        functools.partial(update_inline_loading_indicator, widget),
    )


@textual.work(thread=True)
async def add_repository_archives(
    browse_app, archives_list, config, repository, timer
):
    archives_data = borgmatic.actions.browse.controller.get_repository_archives(config, repository)
    loading_option = archives_list.get_option('loading-indicator')

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    for index, archive in enumerate(reversed(archives_data['archives'])):
        label_pieces = (archive['archive'], '[dim](latest)[/dim]') if index == 0 else (archive['archive'],)
        highlighted_option = archives_list.highlighted_option

        browse_app.call_from_thread(
            archives_list.remove_option,
            'loading-indicator'
        )
        browse_app.call_from_thread(
            archives_list.add_options,
            (
                textual.widgets.option_list.Option(' '.join(label_pieces), id=archive['archive']),
                loading_option,
            )
        )
        archives_list.highlighted = archives_list.get_option_index(highlighted_option.id) if highlighted_option and archives_list.highlighted_option_changed else 0

    browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
    browse_app.call_from_thread(timer.stop)


@textual.work(thread=True)
def add_archive_files(browse_app, directory_list, config, repository, archive_name, list_path, root_directory, timer):
    file_type_paths = borgmatic.actions.browse.controller.get_archive_files(config, repository, archive_name, list_path)
    loading_option = directory_list.get_option('loading-indicator')

    if not root_directory:
        browse_app.call_from_thread(directory_list.remove_option, 'loading-indicator')
        browse_app.call_from_thread(
            directory_list.add_options,
            (
                textual.widgets.option_list.Option(f'{PATH_TYPE_ICONS[Path_type.DIRECTORY.value]} ..', id='..'),
                loading_option,
            )
        )

    for (path_type, file_path, link_target) in file_type_paths:
        pieces = (PATH_TYPE_ICONS.get(path_type, '?'), file_path) + (('→', link_target) if link_target else ())
        highlighted_option = directory_list.highlighted_option
        sorted_options = sorted(
            directory_list.options + [textual.widgets.option_list.Option(' '.join(pieces), id=file_path)],
            key=lambda option: ((option.id == 'loading-indicator'), option.prompt)
        )
        browse_app.call_from_thread(directory_list.set_options, sorted_options)
        directory_list.highlighted = directory_list.get_option_index(highlighted_option.id) if highlighted_option and directory_list.highlighted_option_changed else 0

    browse_app.call_from_thread(timer.stop)
    browse_app.call_from_thread(directory_list.remove_option, 'loading-indicator')


@textual.work(thread=True)
def load_file_preview(browse_app, file_preview, config, repository, archive_name, file_path, timer):
    file_content = borgmatic.actions.browse.controller.get_archive_file_content(config, repository, archive_name, file_path)

    browse_app.call_from_thread(timer.stop)
    syntax_lexer = rich.syntax.Syntax.guess_lexer(file_path, file_content)
    browse_app.call_from_thread(file_preview.update, rich.syntax.Syntax(file_content, syntax_lexer))


OPTION_LIST_BINDINGS = textual.widgets.OptionList.BINDINGS + [
    textual.binding.Binding(key='j', action='cursor_down', description='down', show=False),
    textual.binding.Binding(key='k', action='cursor_up', description='up', show=False),
    textual.binding.Binding(key='right,l', action='select', description='select', show=False),
]


class Configuration_files_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, configs):
        self.configs = configs
        home_directory = os.path.expanduser('~')

        super().__init__(
            *(
                textual.widgets.option_list.Option(f'{unexpanded_path}', id=config_path)
                for config_path in configs.keys()
                for unexpanded_path in (config_path.replace(home_directory, '~'),)

            ),
            classes='panel',
        )
        self.border_title = 'configuration files'

    def make_next_panel(self, option_id):
        return Repositories_list(config=self.configs[option_id])


class Repositories_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config):
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
        self.border_title = 'repositories'

    def make_next_panel(self, option_id):
        return Archives_list(config=self.config, repository=self.repositories[option_id])


class Archives_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config, repository):
        self.config = config
        self.repository = repository

        super().__init__(classes='panel')
        self.border_title = 'archives'
        self.highlighted_option_changed = False

        timer = add_inline_loading_indicator(self)

        add_repository_archives(
            self.app,
            archives_list=self,
            config=self.config,
            repository=self.repository,
            timer=timer,
        )

    def make_next_panel(self, option_id):
        return Directory_list(config=self.config, repository=self.repository, archive_name=option_id)

    def on_option_list_option_highlighted(self, event):
        if self.highlighted not in (None, 0):
            self.highlighted_option_changed = True


class Directory_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config, repository, archive_name, path_components=None):
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.path_components = path_components or ()
        self.highlighted_option_changed = False

        super().__init__(classes='panel')
        self.border_title = os.path.sep.join(self.path_components) if self.path_components else f'{archive_name}'

        timer = add_inline_loading_indicator(self)

        add_archive_files(
            self.app,
            directory_list=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            list_path=os.path.sep.join(self.path_components),
            root_directory=not bool(self.path_components),
            timer=timer,
        )

    def make_next_panel(self, option_id):
        option = self.get_option(option_id)

        if option_id == '..':
            return Null_list()

        if option.prompt.startswith(PATH_TYPE_ICONS[Path_type.DIRECTORY.value]):
            return Directory_list(self.config, self.repository, self.archive_name, path_components=self.path_components + (option_id,))

        return File_preview(self.config, self.repository, self.archive_name, file_path=os.path.sep.join(self.path_components + (option_id,)))

    def on_option_list_option_highlighted(self, event):
        if self.highlighted not in (None, 0):
            self.highlighted_option_changed = True


class Null_list(textual.widgets.OptionList):
    def __init__(self):
        super().__init__(classes='panel')


class File_preview(textual.widgets.Static):
    def __init__(self, config, repository, archive_name, file_path):
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.file_path = file_path
        self.can_focus = True

        super().__init__(classes='panel')
        self.border_title = f'{PATH_TYPE_ICONS[Path_type.FILE.value]} {self.file_path} preview'

        timer = add_inline_loading_indicator(self)
        load_file_preview(
            self.app,
            file_preview=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            file_path=self.file_path,
            timer=timer,
        )

    def make_next_panel(self, option_id):
        return None


class Carousel(textual.containers.Horizontal):
    BINDINGS = [
        textual.binding.Binding(key='left,h', action='previous', description='previous', priority=True),
    ]

    def __init__(self, panels):
        self.panels = panels
        self.focused_panel = panels[0]

        super().__init__()

    def compose(self):
        for panel in self.panels:
            yield panel

        self.focused_panel.focus()

    def action_previous(self):
        '''
        Make the previous panel into the focused panel.
        '''
        previous_panel_index = self.panels.index(self.focused_panel) - 1

        if previous_panel_index < 0:
            return

        self.focused_panel.styles.display = 'none'

        self.focused_panel = self.panels[previous_panel_index]
        self.focused_panel.styles.display = 'block'
        self.focused_panel.focus()

    def action_next(self, option_id):
        '''
        Hide the current focused panel and create the next one.
        '''
        self.focused_panel.styles.display = 'none'
        next_panel_index = self.panels.index(self.focused_panel) + 1

        if next_panel_index < len(self.panels):
            self.focused_panel = self.panels[next_panel_index]
            self.focused_panel.styles.display = 'block'
        else:
            self.focused_panel = self.focused_panel.make_next_panel(option_id)
            self.panels.append(self.focused_panel)
            self.focused_panel.highlighted = 0

        self.focused_panel.focus()
        self.refresh(recompose=True)

    def on_option_list_option_highlighted(self, event):
        '''
        The highlighted option has changed, so truncate any next panels.
        '''
        next_panel_index = self.panels.index(self.focused_panel) + 1

        del(self.panels[next_panel_index:])

    def on_option_list_option_selected(self, event):
        if event.option_list != self.focused_panel or event.option_id == 'loading-indicator':
            return

        if event.option_id == '..':
            self.action_previous()
        else:
            self.action_next(event.option_id)


class Logs(textual.widgets.RichLog):
    def __init__(self):
        super().__init__(markup=True, id='logs', classes='panel')
        self.border_title = 'logs'


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
        yield Carousel([Configuration_files_list(self.configs)])

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
        logs_container = self.query_one('#logs')
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
