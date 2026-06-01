from borgmatic.actions.browse import file_preview as module

from flexmock import flexmock
import textual.widgets.option_list


def test_file_preview_does_not_raise():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')

    module.File_preview(
        config=flexmock(), repository=flexmock(), archive_name='archive', file_path='foo/bar.txt'
    )


async def test_file_preview_on_mount_does_not_raise():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_file_preview')
    file_preview = module.File_preview(
        config=flexmock(), repository=flexmock(), archive_name='archive', file_path='foo.txt'
    )
    flexmock(file_preview.file_preview_loaded).should_receive('subscribe')

    async with textual.app.App().run_test() as pilot:
        file_preview.on_mount()


def test_file_preview_on_file_preview_loaded_with_none_file_contents_displays_error():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator').and_return(flexmock(stop=lambda: None))
    file_preview = module.File_preview(
        config=flexmock(), repository=flexmock(), archive_name='archive', file_path='foo.txt'
    )
    flexmock(file_preview).should_receive('write').with_args('Cannot display a preview for this file').once()

    file_preview.on_file_preview_loaded(None)


def test_file_preview_on_file_preview_loaded_with_file_contents_displays_contents():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator').and_return(flexmock(stop=lambda: None))
    file_preview = module.File_preview(
        config=flexmock(), repository=flexmock(), archive_name='archive', file_path='foo.txt'
    )
    flexmock(file_preview).should_receive('write').with_args('Cannot display a preview for this file').never()
    flexmock(file_preview).should_receive('write').once()

    file_preview.on_file_preview_loaded('hi')
