import contextlib
import functools

import textual.widgets
import textual.widgets.option_list

LOADING_DOT_INTERVAL_SECONDS = 0.3


import logging
logger = logging.getLogger('__name__')


def update_inline_loading_indicator(widget):
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


def add_inline_loading_indicator(widget):
    loading_message = '⏳ loading...'

    if isinstance(widget, textual.widgets.OptionList):
        widget.clear_options()
        loading_option = textual.widgets.option_list.Option(loading_message, id='loading-indicator')
        widget.add_option(loading_option)
        widget.highlighted = None
    elif isinstance(widget, textual.widgets.RichLog):
        widget.write(loading_message)
    else:
        raise ValueError(f'Unsupported widget type: {type(widget)}')

    return widget.set_interval(
        LOADING_DOT_INTERVAL_SECONDS,
        functools.partial(update_inline_loading_indicator, widget),
    )
