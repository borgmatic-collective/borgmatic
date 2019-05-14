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


def should_do_markup(no_color):
    '''
    Determine if we should enable colorama marking up.
    '''
    if no_color:
        return False

    py_colors = os.environ.get('PY_COLORS', None)

    if py_colors is not None:
        return to_bool(py_colors)

    return sys.stdout.isatty() and os.environ.get('TERM') != 'dumb'


LOG_LEVEL_TO_COLOR = {
    logging.CRITICAL: colorama.Fore.RED,
    logging.ERROR: colorama.Fore.RED,
    logging.WARN: colorama.Fore.YELLOW,
    logging.INFO: colorama.Fore.GREEN,
    logging.DEBUG: colorama.Fore.CYAN,
}


class Borgmatic_logger(logging.Logger):
    def critical(self, msg, *args, **kwargs):
        color = LOG_LEVEL_TO_COLOR.get(logging.CRITICAL)

        return super(Borgmatic_logger, self).critical(color_text(color, msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        color = LOG_LEVEL_TO_COLOR.get(logging.ERROR)

        return super(Borgmatic_logger, self).error(color_text(color, msg), *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        color = LOG_LEVEL_TO_COLOR.get(logging.WARN)

        return super(Borgmatic_logger, self).warn(color_text(color, msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        color = LOG_LEVEL_TO_COLOR.get(logging.INFO)

        return super(Borgmatic_logger, self).info(color_text(color, msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        color = LOG_LEVEL_TO_COLOR.get(logging.DEBUG)

        return super(Borgmatic_logger, self).debug(color_text(color, msg), *args, **kwargs)

    def handle(self, record):
        color = LOG_LEVEL_TO_COLOR.get(record.levelno)
        colored_record = logging.makeLogRecord(
            dict(levelno=record.levelno, msg=color_text(color, record.msg))
        )

        return super(Borgmatic_logger, self).handle(colored_record)


def get_logger(name=None):
    '''
    Build a logger with the given name.
    '''
    logging.setLoggerClass(Borgmatic_logger)
    logger = logging.getLogger(name)
    logger.propagate = False
    return logger


def color_text(color, message):
    '''
    Give colored text.
    '''
    if not color:
        return message

    return '{}{}{}'.format(color, message, colorama.Style.RESET_ALL)
