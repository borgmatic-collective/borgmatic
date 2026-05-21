import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.loading
import borgmatic.actions.browse.paths
import borgmatic.actions.browse.workers


OPTION_LIST_BINDINGS = textual.widgets.OptionList.BINDINGS + [
    textual.binding.Binding(key='up,k', action='cursor_up', description='up', show=True, priority=True),
    textual.binding.Binding(key='down,j', action='cursor_down', description='down', show=True, priority=True),
    textual.binding.Binding(key='enter', action='select', description='select', show=True, priority=True),
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


class Archives_list(textual.widgets.OptionList):
    BINDINGS = OPTION_LIST_BINDINGS

    def __init__(self, config, repository):
        self.config = config
        self.repository = repository

        super().__init__(classes='panel')
        self.border_title = 'archives'
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
        if self.highlighted not in (None, 0):
            self.highlighted_option_changed = True


class File_preview(textual.widgets.Static):
    def __init__(self, config, repository, archive_name, file_path):
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.file_path = file_path
        self.can_focus = True

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


def make_next_panel(focused_panel, option_id):
    if isinstance(focused_panel, Configuration_files_list):
        return Repositories_list(config=focused_panel.configs[option_id])

    if isinstance(focused_panel, Repositories_list):
        return Archives_list(config=focused_panel.config, repository=focused_panel.repositories[option_id])

    if isinstance(focused_panel, Archives_list):
        return Directory_list(
            config=focused_panel.config, repository=focused_panel.repository, archive_name=option_id
        )

    if isinstance(focused_panel, Directory_list):
        option = focused_panel.get_option(option_id)

        if option.prompt.startswith(
            borgmatic.actions.browse.paths.PATH_TYPE_ICONS[
                borgmatic.actions.browse.paths.Path_type.DIRECTORY.value
            ]
        ):
            return Directory_list(
                focused_panel.config,
                focused_panel.repository,
                focused_panel.archive_name,
                path_components=focused_panel.path_components + (option_id,),
            )

        return File_preview(
            focused_panel.config,
            focused_panel.repository,
            focused_panel.archive_name,
            file_path=os.path.sep.join(focused_panel.path_components + (option_id,)),
        )

    return None


class Carousel(textual.containers.Horizontal):
    BINDINGS = [
        textual.binding.Binding(
            key='left,h', action='previous', description='previous', priority=True
        ),
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
            self.focused_panel = make_next_panel(self.focused_panel, option_id)
            self.panels.append(self.focused_panel)
            self.focused_panel.highlighted = 0

        self.focused_panel.focus()
        self.refresh(recompose=True)

    def on_option_list_option_highlighted(self, event):
        '''
        The highlighted option has changed, so truncate any next panels.
        '''
        next_panel_index = self.panels.index(self.focused_panel) + 1

        del self.panels[next_panel_index:]

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
