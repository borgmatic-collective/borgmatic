import logging
import logging.handlers
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


def interactive_console():
    '''
    Return whether the current console is "interactive". Meaning: Capable of
    user input and not just something like a cron job.
    '''
    return sys.stderr.isatty() and os.environ.get('TERM') != 'dumb'


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

    return interactive_console()


class Multi_stream_handler(logging.Handler):
    '''
    A logging handler that dispatches each log record to one of multiple stream handlers depending
    on the record's log level.
    '''

    def __init__(self, log_level_to_stream_handler):
        super(Multi_stream_handler, self).__init__()
        self.log_level_to_handler = log_level_to_stream_handler
        self.handlers = set(self.log_level_to_handler.values())

    def flush(self):  # pragma: no cover
        super(Multi_stream_handler, self).flush()

        for handler in self.handlers:
            handler.flush()

    def emit(self, record):
        '''
        Dispatch the log record to the approriate stream handler for the record's log level.
        '''
        self.log_level_to_handler[record.levelno].emit(record)

    def setFormatter(self, formatter):  # pragma: no cover
        super(Multi_stream_handler, self).setFormatter(formatter)

        for handler in self.handlers:
            handler.setFormatter(formatter)

    def setLevel(self, level):  # pragma: no cover
        super(Multi_stream_handler, self).setLevel(level)

        for handler in self.handlers:
            handler.setLevel(level)


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


def configure_logging(
    console_log_level,
    syslog_log_level=None,
    log_file_log_level=None,
    monitoring_log_level=None,
    log_file=None,
):
    '''
    Configure logging to go to both the console and (syslog or log file). Use the given log levels,
    respectively.

    Raise FileNotFoundError or PermissionError if the log file could not be opened for writing.
    '''
    if syslog_log_level is None:
        syslog_log_level = console_log_level
    if log_file_log_level is None:
        log_file_log_level = console_log_level
    if monitoring_log_level is None:
        monitoring_log_level = console_log_level

    # Log certain log levels to console stderr and others to stdout. This supports use cases like
    # grepping (non-error) output.
    console_error_handler = logging.StreamHandler(sys.stderr)
    console_standard_handler = logging.StreamHandler(sys.stdout)
    console_handler = Multi_stream_handler(
        {
            logging.CRITICAL: console_error_handler,
            logging.ERROR: console_error_handler,
            logging.WARN: console_standard_handler,
            logging.INFO: console_standard_handler,
            logging.DEBUG: console_standard_handler,
        }
    )
    console_handler.setFormatter(Console_color_formatter())
    console_handler.setLevel(console_log_level)

    syslog_path = None
    if log_file is None:
        if os.path.exists('/dev/log'):
            syslog_path = '/dev/log'
        elif os.path.exists('/var/run/syslog'):
            syslog_path = '/var/run/syslog'
        elif os.path.exists('/var/run/log'):
            syslog_path = '/var/run/log'

    if syslog_path and not interactive_console():
        syslog_handler = logging.handlers.SysLogHandler(address=syslog_path)
        syslog_handler.setFormatter(logging.Formatter('borgmatic: %(levelname)s %(message)s'))
        syslog_handler.setLevel(syslog_log_level)
        handlers = (console_handler, syslog_handler)
    elif log_file:
        file_handler = logging.handlers.WatchedFileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
        file_handler.setLevel(log_file_log_level)
        handlers = (console_handler, file_handler)
    else:
        handlers = (console_handler,)

    logging.basicConfig(
        level=min(console_log_level, syslog_log_level, log_file_log_level, monitoring_log_level),
        handlers=handlers,
    )
