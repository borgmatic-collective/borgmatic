import logging
import contextlib
import os

import rich.syntax
import textual.binding
import textual.widgets

import borgmatic.actions.browse.loading
import borgmatic.actions.browse.workers


logger = logging.getLogger('__name__')


class File_preview(textual.widgets.RichLog):
    '''
    A widget for extracting and previewing the contents of a file stored in a Borg archive.
    '''

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
        '''
        Given a configuration dict, a repository dict, an archive name, and the path of a file in
        the archive, prepare to load the file's contents for eventual display in this widget. Actual
        loading kicks off in on_mount() below.
        '''
        self.config = config
        self.repository = repository
        self.archive_name = archive_name
        self.file_path = file_path

        super().__init__(classes='panel')
        self.border_title = ' '.join(('📄', self.file_path, 'preview'))
        self.auto_scroll = False
        self.file_preview_loaded = borgmatic.actions.browse.workers.File_preview_loaded(
            self, 'file preview loaded'
        )

        self.loading_timer = borgmatic.actions.browse.loading.add_inline_loading_indicator(self)

    def on_mount(self):
        '''
        When this widget gets mounted in the DOM, subscribe to archive loaded events so that we can
        find out about archives as they load. Also start loading file contents from the archive.

        Loading is started *after* subscribing to the file preview loaded signal so that there's not
        a gap where we might miss out on signal publishes.
        '''
        self.file_preview_loaded.subscribe(self, self.on_file_preview_loaded)

        borgmatic.actions.browse.workers.load_file_preview(
            self.app,
            file_preview_loaded=self.file_preview_loaded,
            config=self.config,
            repository=self.repository,
            archive_name=self.archive_name,
            file_path=self.file_path,
            loading_timer=self.loading_timer,
        )

    def on_file_preview_loaded(self, file_contents):
        '''
        When a file loads, write its contents (syntax highlighted) to this file preview widget.
        '''
        self.loading_timer.stop()
        self.clear()

        if file_contents is None:
            self.write('Cannot display a preview for this file')
        else:
            # Only pass the file path and not its contents to guess_lexer(). Passing the contents is
            # more accurate, but also much slower.
            self.write(
                rich.syntax.Syntax(file_contents, rich.syntax.Syntax.guess_lexer(self.file_path))
            )
