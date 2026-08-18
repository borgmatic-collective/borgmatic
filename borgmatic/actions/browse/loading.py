import contextlib
import functools
import logging

import textual.widgets
import textual.widgets.option_list

LOADING_DOT_INTERVAL_SECONDS = 0.3


logger = logging.getLogger('__name__')


def update_inline_loading_indicator(widget):
    '''
    Given a textual.widgets.OptionList or a textual.widgets.RichLog instance, animate the existing
    loading indicator inside it.
    '''
    if isinstance(widget, textual.widgets.OptionList):
        with contextlib.suppress(textual.widgets.option_list.OptionDoesNotExist):
            widget.replace_option_prompt(
                'loading-indicator',
                (str(widget.get_option('loading-indicator').prompt) + '.').replace('....', ''),
            )
    elif isinstance(widget, textual.widgets.RichLog):
        with contextlib.suppress(IndexError):
            loading_message = str(widget.lines[0].text)
            widget.clear()
            widget.write((loading_message + '.').replace('....', ''))
    else:
        raise ValueError(f'Unsupported widget type: {type(widget)}')


LOADING_MESSAGE = '⏳ loading...'


def add_inline_loading_indicator(widget):
    '''
    Given a textual.widgets.OptionList or a textual.widgets.RichLog instance, add a loading
    indicator to it.
    '''
    if isinstance(widget, textual.widgets.OptionList):
        loading_option = textual.widgets.option_list.Option(LOADING_MESSAGE, id='loading-indicator')
        widget.add_option(loading_option)
        widget.highlighted = None
    elif isinstance(widget, textual.widgets.RichLog):
        widget.write(LOADING_MESSAGE)
    else:
        raise ValueError(f'Unsupported widget type: {type(widget)}')

    return widget.set_interval(
        LOADING_DOT_INTERVAL_SECONDS,
        functools.partial(update_inline_loading_indicator, widget),
    )
