import os

import textual.binding
import textual.containers

import borgmatic.actions.browse.panels
import borgmatic.actions.browse.paths


def make_next_panel(focused_panel, option_id):
    if isinstance(focused_panel, borgmatic.actions.browse.panels.Configuration_files_list):
        return borgmatic.actions.browse.panels.Repositories_list(
            config=focused_panel.configs[option_id]
        )

    if isinstance(focused_panel, borgmatic.actions.browse.panels.Repositories_list):
        return borgmatic.actions.browse.panels.Archives_list(
            config=focused_panel.config, repository=focused_panel.repositories[option_id]
        )

    if isinstance(focused_panel, borgmatic.actions.browse.panels.Archives_list):
        return borgmatic.actions.browse.panels.Directory_list(
            config=focused_panel.config, repository=focused_panel.repository, archive_name=option_id
        )

    if isinstance(focused_panel, borgmatic.actions.browse.panels.Directory_list):
        option = focused_panel.get_option(option_id)

        if option.prompt.startswith(
            borgmatic.actions.browse.paths.PATH_TYPE_ICONS[
                borgmatic.actions.browse.paths.Path_type.DIRECTORY.value
            ]
        ):
            return borgmatic.actions.browse.panels.Directory_list(
                focused_panel.config,
                focused_panel.repository,
                focused_panel.archive_name,
                path_components=(*focused_panel.path_components, option_id),
            )

        return borgmatic.actions.browse.panels.File_preview(
            focused_panel.config,
            focused_panel.repository,
            focused_panel.archive_name,
            file_path=os.path.sep.join((*focused_panel.path_components, option_id)),
        )

    return None


class Carousel(textual.containers.Horizontal):
    BINDINGS = (
        textual.binding.Binding(
            key='left,h', action='previous', description='previous', priority=True
        ),
    )

    def __init__(self, panels):
        self.panels = panels
        self.focused_panel = panels[0]

        super().__init__()

    def compose(self):
        yield from self.panels

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
