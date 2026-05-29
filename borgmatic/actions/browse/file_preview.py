import contextlib
import os

import textual.binding
import textual.widgets

import borgmatic.actions.browse.archive
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.icons
import borgmatic.actions.browse.workers


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
                borgmatic.actions.browse.icons.PATH_TYPE_ICONS[
                    borgmatic.actions.browse.archive.Path_type.FILE.value
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
