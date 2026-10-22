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

    For an option list, keep the loading indicator option's prompt_text in sync with its animated
    prompt.
    '''
    if isinstance(widget, textual.widgets.OptionList):
        with contextlib.suppress(textual.widgets.option_list.OptionDoesNotExist):
            loading_option = widget.get_option('loading-indicator')
            loading_message = (str(loading_option.prompt) + '.').replace('....', '')
            widget.replace_option_prompt('loading-indicator', loading_message)
            loading_option.prompt_text = loading_message
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

    For an option list, also stash the loading message on the loading indicator option as
    prompt_text, so that consumers can get the plain text of any option's prompt from prompt_text
    regardless of whether it's an ordinary string or a Rich renderable.
    '''
    if isinstance(widget, textual.widgets.OptionList):
        loading_option = textual.widgets.option_list.Option(LOADING_MESSAGE, id='loading-indicator')
        loading_option.prompt_text = LOADING_MESSAGE
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
