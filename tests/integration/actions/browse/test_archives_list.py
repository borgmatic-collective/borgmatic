import textual.app
import textual.widgets.option_list
from flexmock import flexmock

from borgmatic.actions.browse import archives_list as module


async def test_archives_list_on_mount_does_not_raise():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.workers).should_receive('add_repository_archives')
    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    flexmock(archives_list.archive_loaded).should_receive('subscribe')

    async with textual.app.App().run_test():
        archives_list.on_mount()


def test_archives_list_on_archive_loaded_with_loading_done_removes_loading_indicator():
    loading_timer = flexmock()
    flexmock(module.borgmatic.actions.browse.loading).should_receive(
        'add_inline_loading_indicator'
    ).and_return(loading_timer)
    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    flexmock(loading_timer).should_receive('stop')
    flexmock(archives_list).should_receive('remove_option').with_args('loading-indicator').once()
    flexmock(archives_list).should_receive('add_options').never()

    archives_list.on_archive_loaded(module.borgmatic.actions.browse.workers.LOADING_DONE)


def test_archives_list_on_archive_loaded_adds_archive_name():
    loading_timer = flexmock()
    flexmock(module.borgmatic.actions.browse.loading).should_receive(
        'add_inline_loading_indicator'
    ).and_return(loading_timer)
    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    flexmock(loading_timer).should_receive('stop').never()
    loading_indicator = flexmock()
    flexmock(archives_list).should_receive('get_option').and_return(loading_indicator)
    flexmock(archives_list).should_receive('remove_option').with_args('loading-indicator').once()
    flexmock(archives_list).should_receive('add_options').once()

    archives_list.on_archive_loaded('archive')


def test_archives_list_on_option_list_option_highlighted_with_highlighted_none_marks_it_unchanged():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')

    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    archives_list.highlighted = None
    archives_list.on_option_list_option_highlighted(event=flexmock())

    assert archives_list.highlighted_option_changed is False


def test_archives_list_on_option_list_option_highlighted_with_highlighted_zero_marks_it_unchanged():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')

    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    archives_list.highlighted = 0
    archives_list.on_option_list_option_highlighted(event=flexmock())

    assert archives_list.highlighted_option_changed is False


def test_archives_list_on_option_list_option_highlighted_with_existing_option_and_highlighted_zero_marks_it_unchanged():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')

    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    archives_list.add_option(textual.widgets.option_list.Option('zero', id='zero'))
    archives_list.highlighted = 0
    archives_list.on_option_list_option_highlighted(event=flexmock())

    assert archives_list.highlighted_option_changed is False


def test_archives_list_on_option_list_option_highlighted_with_highlighted_non_zero_marks_it_changed():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')

    archives_list = module.Archives_list(config=flexmock(), repository=flexmock())
    archives_list.add_option(textual.widgets.option_list.Option('zero', id='zero'))
    archives_list.add_option(textual.widgets.option_list.Option('one', id='one'))
    archives_list.highlighted = 1
    archives_list.on_option_list_option_highlighted(event=flexmock())

    assert archives_list.highlighted_option_changed is True
