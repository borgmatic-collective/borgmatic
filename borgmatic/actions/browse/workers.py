import rich.syntax
import textual
import textual.widgets.option_list

import borgmatic.actions.browse.archive


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
        archives_list.highlighted = (
            archives_list.get_option_index(highlighted_option.id)
            if highlighted_option and archives_list.highlighted_option_changed
            else 0
        )

    browse_app.call_from_thread(archives_list.remove_option, 'loading-indicator')
    browse_app.call_from_thread(timer.stop)


@textual.work(thread=True)
def add_archive_files(
    browse_app, directory_list, config, repository, archive_name, list_path, root_directory, timer
):
    file_type_paths = borgmatic.actions.browse.archive.get_archive_files(
        config, repository, archive_name, list_path
    )
    loading_option = directory_list.get_option('loading-indicator')

    if not root_directory:
        browse_app.call_from_thread(directory_list.remove_option, 'loading-indicator')
        browse_app.call_from_thread(
            directory_list.add_options,
            (
                textual.widgets.option_list.Option(
                    f'{borgmatic.actions.browse.paths.PATH_TYPE_ICONS[borgmatic.actions.browse.paths.Path_type.DIRECTORY.value]} ..',
                    id='..',
                ),
                loading_option,
            ),
        )

    for path_type, file_path, link_target in file_type_paths:
        pieces = (
            borgmatic.actions.browse.paths.PATH_TYPE_ICONS.get(path_type, '❓'),
            file_path,
        ) + (('→', link_target) if link_target else ())
        highlighted_option = directory_list.highlighted_option
        sorted_options = sorted(
            [
                *directory_list.options,
                textual.widgets.option_list.Option(' '.join(pieces), id=file_path),
            ],
            key=lambda option: ((option.id == 'loading-indicator'), option.prompt),
        )
        browse_app.call_from_thread(directory_list.set_options, sorted_options)
        directory_list.highlighted = (
            directory_list.get_option_index(highlighted_option.id)
            if highlighted_option and directory_list.highlighted_option_changed
            else 0
        )

    browse_app.call_from_thread(timer.stop)
    browse_app.call_from_thread(directory_list.remove_option, 'loading-indicator')


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
