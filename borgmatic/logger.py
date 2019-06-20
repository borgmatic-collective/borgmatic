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


def should_do_markup(no_color, configs):
    '''
    Given the value of the command-line no-color argument, and a dict of configuration filename to
    corresponding parsed configuration, determine if we should enable colorama marking up.
    '''
    if no_color:
        return False

    if any(config.get('output', {}).get('color') is False for config in configs.values()):
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


class Console_color_formatter(logging.Formatter):
    def format(self, record):
        color = LOG_LEVEL_TO_COLOR.get(record.levelno)
        return color_text(color, record.msg)


def color_text(color, message):
    '''
    Give colored text.
    '''
    if not color:
        return message

    return '{}{}{}'.format(color, message, colorama.Style.RESET_ALL)


def configure_logging(console_log_level, syslog_log_level=None):
    '''
    Configure logging to go to both the console and syslog. Use the given log levels, respectively.
    '''
    if syslog_log_level is None:
        syslog_log_level = console_log_level

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(Console_color_formatter())
    console_handler.setLevel(console_log_level)

    syslog_path = None
    if os.path.exists('/dev/log'):
        syslog_path = '/dev/log'
    elif os.path.exists('/var/run/syslog'):
        syslog_path = '/var/run/syslog'

    if syslog_path:
        syslog_handler = logging.handlers.SysLogHandler(address=syslog_path)
        syslog_handler.setFormatter(logging.Formatter('borgmatic: %(levelname)s \ufeff%(message)s'))
        syslog_handler.setLevel(syslog_log_level)
        handlers = (console_handler, syslog_handler)
    else:
        handlers = (console_handler,)

    logging.basicConfig(level=min(console_log_level, syslog_log_level), handlers=handlers)
