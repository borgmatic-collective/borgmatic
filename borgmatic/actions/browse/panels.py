import contextlib
import logging
import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.loading
import borgmatic.actions.browse.paths
import borgmatic.actions.browse.workers


logger = logging.getLogger('__name__')


OPTION_LIST_BINDINGS = (
    *textual.widgets.OptionList.BINDINGS,
    textual.binding.Binding(
        key='up,k', action='cursor_up', description='scroll up', show=True, priority=True
    ),
    textual.binding.Binding(
        key='down,j', action='cursor_down', description='scroll down', show=True, priority=True
    ),
    textual.binding.Binding(
        key='pageup', action='page_up', description='page up', show=True, priority=True
    ),
    textual.binding.Binding(
        key='pagedown', action='page_down', description='page down', show=True, priority=True
    ),
    textual.binding.Binding(
        key='enter', action='select', description='select', show=True, priority=True
    ),
    textual.binding.Binding(key='right,l', action='select', description='select', show=False),
)


class Configuration_files_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

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
        self.border_title = '📦 repositories'


class Archives_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config, repository):
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
        if self.highlighted not in {None, 0}:
            self.highlighted_option_changed = True


def add_archive_path(
    directory_list,
    config,
    repository,
    archive_name,
    archive_path,
):
    archive_path_components = archive_path.file_path.split(os.path.sep)

    if directory_list.path_components:
        # If the loaded path doesn't match this directory list's own path, then we don't care about
        # it for purposes of displaying this particular directory.
        if tuple(archive_path_components[: len(directory_list.path_components)]) != directory_list.path_components:
            return

        # Strip off the portion of the archive path that matches the directory list's own path.
        archive_path_components = archive_path_components[len(directory_list.path_components):]

    base_path = archive_path_components[0]

    # If the option is already in the list, bail.
    with contextlib.suppress(textual.widgets.option_list.OptionDoesNotExist):
        directory_list.get_option(option_id=base_path)

        return

    pieces = (
        borgmatic.actions.browse.paths.PATH_TYPE_ICONS.get(
            archive_path.path_type if len(archive_path_components) == 1 else 'd', '❓'
        ),
        base_path,
    ) + (('→', archive_path.link_target) if archive_path.link_target else ())
    highlighted_option = directory_list.highlighted_option
    sorted_options = sorted(
        [
            *directory_list.options,
            textual.widgets.option_list.Option(' '.join(pieces), id=base_path),
        ],
        key=lambda option: ((option.id == 'loading-indicator'), option.prompt),
    )

    directory_list.set_options(sorted_options)
    directory_list.highlighted = (
        directory_list.get_option_index(highlighted_option.id)
        if highlighted_option and directory_list.highlighted_option_changed
        else 0
    )


class Directory_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config, repository, archive_name, path_loaded=None, path_components=None):
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.path_components = path_components or ()
        self.highlighted_option_changed = False

        super().__init__(classes='panel')

        self.border_title = ' '.join(
            (
                borgmatic.actions.browse.paths.PATH_TYPE_ICONS[
                    borgmatic.actions.browse.paths.Path_type.DIRECTORY.value
                ],
                os.path.sep.join(self.path_components)
                if self.path_components
                else f'{archive_name}',
            )
        )

        # FIXME: This isn't working when loading is still underway??? I don't see a ".."
        if self.path_components:
            self.add_option(
                textual.widgets.option_list.Option(
                    f'{borgmatic.actions.browse.paths.PATH_TYPE_ICONS[borgmatic.actions.browse.paths.Path_type.DIRECTORY.value]} ..',
                    id='..',
                ),
            )

        self.path_loaded = path_loaded or borgmatic.actions.browse.workers.Archive_path_loaded(
            self, 'archive path loaded'
        )

        if not self.path_loaded.complete:
            # FIXME: After going back to a previous panel, the loading indicator is no longer animating.
            self.timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

        if self.path_components:
            for archive_path in borgmatic.actions.browse.workers.get_paths(
                self.path_loaded.path_hierarchy, self.path_components
            ):
                self.on_archive_path_loaded(archive_path)
        else:
            borgmatic.actions.browse.workers.load_archive_files(
                self.app,
                directory_list=self,
                config=self.config,
                repository=self.repository,
                archive_name=self.archive_name,
            )

    def on_mount(self):
        self.path_loaded.subscribe(self, self.on_archive_path_loaded)

    def on_archive_path_loaded(self, data):
        if data is borgmatic.actions.browse.workers.LOADING_DONE:
            self.timer.stop()
            self.remove_option('loading-indicator')
            return

        add_archive_path(
            directory_list=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            archive_path=data,
        )

    def on_option_list_option_highlighted(self, event):
        if self.highlighted not in {None, 0}:
            self.highlighted_option_changed = True


class File_preview(textual.widgets.RichLog):
    BINDINGS = [
        *textual.widgets.RichLog.BINDINGS,
        textual.binding.Binding(
            key='up,k', action='scroll_up', description='scroll up', show=True, priority=True
        ),
        textual.binding.Binding(
            key='down,j', action='scroll_down', description='scroll down', show=True, priority=True
        ),
        textual.binding.Binding(
            key='pageup', action='page_up', description='page up', show=True, priority=True
        ),
        textual.binding.Binding(
            key='pagedown', action='page_down', description='page down', show=True, priority=True
        ),
    ]

    def __init__(self, config, repository, archive_name, file_path):
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.file_path = file_path

        super().__init__(classes='panel')
        self.border_title = ' '.join(
            (
                borgmatic.actions.browse.paths.PATH_TYPE_ICONS[
                    borgmatic.actions.browse.paths.Path_type.FILE.value
                ],
                self.file_path,
                'preview',
            )
        )
        self.auto_scroll = False

        timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

        borgmatic.actions.browse.workers.load_file_preview(
            self.app,
            file_preview=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            file_path=self.file_path,
            timer=timer,
        )


class Logs(textual.widgets.RichLog):
    def __init__(self):
        super().__init__(markup=True, id='logs', classes='panel')
        self.border_title = '🪵 logs'
