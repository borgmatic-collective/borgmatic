from borgmatic.actions.browse import archives_list as module

from flexmock import flexmock
import textual.widgets.option_list


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


def test_archives_list_on_option_list_option_highlighted_with_highlighted_zero_marks_it_unchanged():
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
