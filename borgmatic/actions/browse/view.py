import contextlib
import enum
import functools
import os
import logging

import borgmatic.actions.browse.controller

import rich.text
import textual._context
import textual.app
import textual.binding
import textual.reactive
import textual.widgets


class Node_type(enum.Enum):
    CONFIGURATION = 0
    REPOSITORY = 1
    ARCHIVE = 2
    DIRECTORY = 3
    FILE = 4
    DUMP = 5
    BOOTSTRAP = 6
    LOADING = 7


PATH_TYPE_ICONS = {
    Node_type.CONFIGURATION: '⚙️ ',
    Node_type.REPOSITORY: '🗃️ ',
    Node_type.ARCHIVE: '🗂️ ',
    Node_type.DIRECTORY: '📁',
    Node_type.FILE: '📄',
    Node_type.DUMP: '🗄️',
    Node_type.BOOTSTRAP: '🥾',
    Node_type.LOADING: '⏳',
}


PATH_TYPE_EXPANDED_ICONS = {Node_type.DIRECTORY: '📂'}


@textual.work(thread=True)
async def get_repository_archives(browse_tree, repository_node, config, repository, timer):
    archives_data = borgmatic.actions.browse.controller.get_repository_archives(config, repository)

    browse_tree.app.call_from_thread(add_repository_archives, repository_node, archives_data, timer)


def add_repository_archives(repository_node, archives_data, timer):
    timer.stop()

    for child in repository_node.children:
        child.remove()

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    for archive in reversed(archives_data['archives']):
        repository_node.add(
            archive['archive'],
            data={
                'type': Node_type.ARCHIVE,
                'config': repository_node.data['config'],
                'repository': repository_node.data['repository'],
                'archive': archive,
            },
        )


@textual.work(thread=True)
def get_archive_files(browse_tree, archive_node, config, repository, archive, timer):
    files_data = borgmatic.actions.browse.controller.get_archive_files(config, repository, archive)

    browse_tree.app.call_from_thread(add_archive_files, archive_node, files_data, timer)


def add_archive_files(archive_node, files_data, timer):
    config = archive_node.data['config']
    repository = archive_node.data['repository']
    archive = archive_node.data['archive']

    timer.stop()

    for child in archive_node.children:
        child.remove()

    for file in files_data:
        archive_node.add(
            file['path'],
            data={
                'type': Node_type.DIRECTORY if file['type'] == 'd' else Node_type.FILE,
                'config': config,
                'repository': repository,
                'archive': archive,
                'file': file,
            },
        )


class Browse_tree(textual.widgets.Tree):
    COMPONENT_CLASSES = textual.widgets.DirectoryTree.COMPONENT_CLASSES
    DEFAULT_CSS = textual.widgets.DirectoryTree.DEFAULT_CSS
    LOADING_DOT_INTERVAL_SECONDS = 0.3

    def __init__(self):
        super().__init__('root')

        self.show_root = False

    def render_label(self, node, base_style, style):
        node_label = node._label.copy()
        node_label.stylize(style)

        if not self.is_mounted:
            return node_label

        if node._allow_expand:
            icon = PATH_TYPE_ICONS.get(node.data['type'] if node.data else Node_type.FILE)
            expanded_icon = PATH_TYPE_EXPANDED_ICONS.get(
                node.data['type'] if node.data else Node_type.FILE, icon
            )
            prefix = (f'{expanded_icon} ' if node.is_expanded else f'{icon} ', base_style)
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--folder", partial=True)
            )
        else:
            prefix = (f'{PATH_TYPE_ICONS.get(node.data["type"])} ', base_style)
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--file", partial=True),
            )
            node_label.highlight_regex(
                r"\..+$",
                self.get_component_rich_style("directory-tree--extension", partial=True),
            )

        if node_label.plain.startswith('.'):
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--hidden", partial=True)
            )

        return rich.text.Text.assemble(prefix, node_label)

    def update_loading_dots(self, loading_node):
        loading_node.label = (str(loading_node.label) + '.').replace('....', '')

    def on_tree_node_expanded(self, event):
        if event.node.data['type'] == Node_type.REPOSITORY and len(event.node.children) == 0:
            loading_node = event.node.add_leaf(
                'Loading archives...', data={'type': Node_type.LOADING}
            )
            timer = self.set_interval(
                self.LOADING_DOT_INTERVAL_SECONDS,
                functools.partial(self.update_loading_dots, loading_node=loading_node),
            )
            self.call_after_refresh(
                functools.partial(
                    get_repository_archives,
                    self,
                    repository_node=event.node,
                    config=event.node.data['config'],
                    repository=event.node.data['repository'],
                    timer=timer,
                )
            )
        elif event.node.data['type'] == Node_type.ARCHIVE and len(event.node.children) == 0:
            loading_node = event.node.add_leaf('Loading files...', data={'type': Node_type.LOADING})
            timer = self.set_interval(
                self.LOADING_DOT_INTERVAL_SECONDS,
                functools.partial(self.update_loading_dots, loading_node=loading_node),
            )
            self.call_after_refresh(
                functools.partial(
                    get_archive_files,
                    self,
                    archive_node=event.node,
                    config=event.node.data['config'],
                    repository=event.node.data['repository'],
                    archive=event.node.data['archive'],
                    timer=timer,
                )
            )


def unexpand_path(config_path):
    home_directory = os.path.expanduser('~')

    if config_path.startswith(home_directory):
        return config_path.replace(home_directory, '~')

    return config_path


class Browse_app(textual.app.App):
    BINDINGS = [
        textual.binding.Binding(key='escape', action='quit', description='quit'),
        textual.binding.Binding(
            key='alt+m', action='command_palette', description='menu', show=False
        ),
    ]
    COMMAND_PALETTE_BINDING = 'alt+m'

    def __init__(self, configs):
        self.configs = configs

        super().__init__()

    def compose(self):
        tree = Browse_tree()
        tree.styles.border = ('round', 'gray')

        for config_path, config in self.configs.items():
            config_node = tree.root.add(
                unexpand_path(config_path), data={'type': Node_type.CONFIGURATION, 'config': config}
            )

            for repository in config['repositories']:
                config_node.add(
                    repository['path'],
                    data={'type': Node_type.REPOSITORY, 'config': config, 'repository': repository},
                )

        first_child = tree.root.children[0]
        tree.select_node(first_child)
        tree.scroll_to_node(first_child)

        yield textual.widgets.Header()
        yield tree
        log_widget = textual.widgets.RichLog(markup=True)
        log_widget.styles.border = ('round', 'gray')
        yield log_widget
        yield textual.widgets.Footer()

        handler = Browse_log_handler(self, log_widget)
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
        self.theme = 'ansi-light'
        tree = self.query_one(textual.widgets.Tree)

        for child in tree.root.children:
            child.expand()


class Browse_log_handler(logging.Handler):
    def __init__(self, app, log_widget):
        self.app = app
        self.log_widget = log_widget

        super().__init__()

    def emit(self, record):
        message = self.format(record)

        try:
            worker = textual.worker.get_current_worker()
            self.app.call_from_thread(self.log_widget.write, message)
        except textual.worker.NoActiveWorker:
            with contextlib.suppress(textual._context.NoActiveAppError):
                self.log_widget.write(message)


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
