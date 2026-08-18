import pytest
import textual.app
import textual.widgets
from flexmock import flexmock

from borgmatic.actions.browse import loading as module


def test_update_inline_loading_indicator_with_option_list_adds_a_dot():
    widget = textual.widgets.OptionList()
    widget.add_option(textual.widgets.option_list.Option('HOLD.', id='loading-indicator'))

    module.update_inline_loading_indicator(widget)

    assert len(widget.options) == 1
    assert widget.options[0].prompt == 'HOLD..'


def test_update_inline_loading_indicator_with_option_list_wraps_dots_beyond_three():
    widget = textual.widgets.OptionList()
    widget.add_option(textual.widgets.option_list.Option('HOLD...', id='loading-indicator'))

    module.update_inline_loading_indicator(widget)

    assert len(widget.options) == 1
    assert widget.options[0].prompt == 'HOLD'


def test_update_inline_loading_indicator_with_option_list_and_missing_indicator_does_not_raise():
    widget = textual.widgets.OptionList()

    module.update_inline_loading_indicator(widget)

    assert len(widget.options) == 0


async def test_update_inline_loading_indicator_with_rich_log_adds_a_dot():
    async with textual.app.App().run_test():
        widget = textual.widgets.RichLog()
        widget._size_known = True
        widget.write('HOLD.')

        module.update_inline_loading_indicator(widget)

    assert str(widget.lines[0].text) == 'HOLD..'


async def test_update_inline_loading_indicator_with_rich_log_wraps_dots_beyond_three():
    async with textual.app.App().run_test():
        widget = textual.widgets.RichLog()
        widget._size_known = True
        widget.write('HOLD...')

        module.update_inline_loading_indicator(widget)

    assert str(widget.lines[0].text) == 'HOLD'


def test_update_inline_loading_indicator_with_rich_log_and_missing_indicator_does_not_raise():
    widget = textual.widgets.RichLog()

    module.update_inline_loading_indicator(widget)

    assert len(widget.lines) == 0


def test_update_inline_loading_indicator_with_unsupported_widget_type_raises():
    with pytest.raises(ValueError):
        module.update_inline_loading_indicator(flexmock())


def test_add_inline_loading_indicator_with_option_list_adds_loading_indicator_option():
    widget = textual.widgets.OptionList()
    flexmock(widget).should_receive('set_interval')

    module.add_inline_loading_indicator(widget)

    assert len(widget.options) == 1
    assert widget.options[0].prompt == module.LOADING_MESSAGE
    assert widget.options[0].id == 'loading-indicator'
    assert widget.highlighted is None


async def test_add_inline_loading_indicator_with_rich_log_writes_loading_indicator_text():
    async with textual.app.App().run_test():
        widget = textual.widgets.RichLog()
        widget._size_known = True
        flexmock(widget).should_receive('set_interval')

        module.add_inline_loading_indicator(widget)

    assert str(widget.lines[0].text) == module.LOADING_MESSAGE


def test_add_inline_loading_indicator_with_unsupported_widget_type_raises():
    with pytest.raises(ValueError):
        module.add_inline_loading_indicator(flexmock())
