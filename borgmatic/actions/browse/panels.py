import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.loading
import borgmatic.actions.browse.paths
import borgmatic.actions.browse.workers

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


class Directory_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config, repository, archive_name, path_components=None):
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

        timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

        borgmatic.actions.browse.workers.add_archive_files(
            self.app,
            directory_list=self,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            list_path=os.path.sep.join(self.path_components),
            root_directory=not bool(self.path_components),
            timer=timer,
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
