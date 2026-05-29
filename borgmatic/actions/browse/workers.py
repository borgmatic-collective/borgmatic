import contextlib
import logging
import os

import rich.syntax
import textual
import textual.signal
import textual.widgets.option_list

import borgmatic.actions.browse.archive


logger = logging.getLogger('__name__')


@textual.work(thread=True)
def add_repository_archives(browse_app, archives_list, config, repository, timer):
    archives_data = borgmatic.actions.browse.archive.get_repository_archives(config, repository)
    loading_option = archives_list.get_option('loading-indicator')

    # Reverse the archives, so the common case of accessing the latest archive is easy because it's
    # at the top.
    for index, archive in enumerate(reversed(archives_data['archives'])):
        label_pieces = (
            (archive['archive'], '[dim](latest)[/dim]') if index == 0 else (archive['archive'],)
        )
        highlighted_option = archives_list.highlighted_option

        browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
        browse_app.call_from_thread(
            archives_list.add_options,
            (
                textual.widgets.option_list.Option(' '.join(label_pieces), id=archive['archive']),
                loading_option,
            ),
        )

        # Retain the highlighted option position even as other options load around it.
        archives_list.highlighted = (
            archives_list.get_option_index(highlighted_option.id)
            if highlighted_option and archives_list.highlighted_option_changed
            else 0
        )

    browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
    browse_app.call_from_thread(timer.stop)


def record_path(archive_path, hierarchy, path_components):
    if len(path_components) == 1:
        hierarchy[path_components[0]] = {} if archive_path.path_type == 'd' else archive_path
        return

    record_path(archive_path, hierarchy.setdefault(path_components[0], {}), path_components[1:])


def get_paths(hierarchy, path_components, full_path_components=None):
    if full_path_components is None:
        full_path_components = path_components

    if len(path_components) == 1:
        return (
            archive_path
            if isinstance(archive_path, borgmatic.actions.browse.archive.Archive_path)
            else borgmatic.actions.browse.archive.Archive_path(
                'd', os.path.join(*full_path_components, component), ''
            )
            for component, archive_path in hierarchy[path_components[0]].items()
        )

    return get_paths(hierarchy[path_components[0]], path_components[1:], full_path_components)


LOADING_DONE = object()


class Archive_path_loaded(textual.signal.Signal):
    def __init__(self, owner, name):
        self.path_hierarchy = {}
        self.complete = False

        super().__init__(owner, name)

    def publish(self, data):
        super().publish(data)

        if data is LOADING_DONE:
            self.complete = True
        else:
            record_path(data, self.path_hierarchy, data.file_path.split(os.path.sep))


@textual.work(thread=True)
def load_archive_paths(browse_app, directory_list, config, repository, archive_name):
    for archive_path in borgmatic.actions.browse.archive.get_archive_paths(
        config, repository, archive_name
    ):
        directory_list.path_loaded.publish(archive_path)

    directory_list.path_loaded.publish(LOADING_DONE)


@textual.work(thread=True)
def load_file_preview(browse_app, file_preview, config, repository, archive_name, file_path, timer):
    file_content = borgmatic.actions.browse.archive.get_archive_file_content(
        config, repository, archive_name, file_path
    )

    browse_app.call_from_thread(timer.stop)
    browse_app.call_from_thread(file_preview.clear)

    if file_content is None:
        browse_app.call_from_thread(file_preview.write, 'Cannot display a preview for this file')
    else:
        syntax_lexer = rich.syntax.Syntax.guess_lexer(file_path, file_content)
        browse_app.call_from_thread(
            file_preview.write, rich.syntax.Syntax(file_content, syntax_lexer)
        )
