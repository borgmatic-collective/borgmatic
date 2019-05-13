import logging
import os
import sys

import colorama


def to_bool(arg):
    '''
    Return a boolean value based on `arg`.
    '''
    if arg is None or isinstance(arg, bool):
        return arg

    if isinstance(arg, str):
        arg = arg.lower()

    if arg in ('yes', 'on', '1', 'true', 1):
        return True

    return False


def should_do_markup(no_colour):
    '''
    Determine if we should enable colorama marking up.
    '''
    if no_colour:
        return False

    py_colors = os.environ.get('PY_COLORS', None)

    if py_colors is not None:
        return to_bool(py_colors)

    return sys.stdout.isatty() and os.environ.get('TERM') != 'dumb'


class BorgmaticLogger(logging.Logger):
    def warn(self, msg, *args, **kwargs):
        return super(BorgmaticLogger, self).warn(
            color_text(colorama.Fore.YELLOW, msg), *args, **kwargs
        )

    def info(self, msg, *args, **kwargs):
        return super(BorgmaticLogger, self).info(
            color_text(colorama.Fore.GREEN, msg), *args, **kwargs
        )

    def debug(self, msg, *args, **kwargs):
        return super(BorgmaticLogger, self).debug(
            color_text(colorama.Fore.CYAN, msg), *args, **kwargs
        )

    def critical(self, msg, *args, **kwargs):
        return super(BorgmaticLogger, self).critical(
            color_text(colorama.Fore.RED, msg), *args, **kwargs
        )


def get_logger(name=None):
    '''
    Build a logger with the given name.
    '''
    logging.setLoggerClass(BorgmaticLogger)
    logger = logging.getLogger(name)
    logger.propagate = False
    return logger


def color_text(color, msg):
    '''
    Give colored text.
    '''
    return '{}{}{}'.format(color, msg, colorama.Style.RESET_ALL)
