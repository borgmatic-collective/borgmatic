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

    if any(config.get('color', True) is False for config in configs.values()):
        return False

    if os.environ.get('NO_COLOR', None):
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
        Dispatch the log record to the appropriate stream handler for the record's log level.
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


class Console_no_color_formatter(logging.Formatter):
    def format(self, record):  # pragma: no cover
        return record.msg


class Console_color_formatter(logging.Formatter):
    def format(self, record):
        add_custom_log_levels()

        color = {
            logging.CRITICAL: colorama.Fore.RED,
            logging.ERROR: colorama.Fore.RED,
            logging.WARN: colorama.Fore.YELLOW,
            logging.ANSWER: colorama.Fore.MAGENTA,
            logging.INFO: colorama.Fore.GREEN,
            logging.DEBUG: colorama.Fore.CYAN,
        }.get(record.levelno)

        return color_text(color, record.msg)


def color_text(color, message):
    '''
    Give colored text.
    '''
    if not color:
        return message

    return f'{color}{message}{colorama.Style.RESET_ALL}'


def add_logging_level(level_name, level_number):
    '''
    Globally add a custom logging level based on the given (all uppercase) level name and number.
    Do this idempotently.

    Inspired by https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
    '''
    method_name = level_name.lower()

    if not hasattr(logging, level_name):
        logging.addLevelName(level_number, level_name)
        setattr(logging, level_name, level_number)

    if not hasattr(logging, method_name):

        def log_for_level(self, message, *args, **kwargs):  # pragma: no cover
            if self.isEnabledFor(level_number):
                self._log(level_number, message, args, **kwargs)

        setattr(logging.getLoggerClass(), method_name, log_for_level)

    if not hasattr(logging.getLoggerClass(), method_name):

        def log_to_root(message, *args, **kwargs):  # pragma: no cover
            logging.log(level_number, message, *args, **kwargs)

        setattr(logging, method_name, log_to_root)


ANSWER = logging.WARN - 5
DISABLED = logging.CRITICAL + 10


def add_custom_log_levels():  # pragma: no cover
    '''
    Add a custom log level between WARN and INFO for user-requested answers.
    '''
    add_logging_level('ANSWER', ANSWER)
    add_logging_level('DISABLED', DISABLED)


def configure_logging(
    console_log_level,
    syslog_log_level=None,
    log_file_log_level=None,
    monitoring_log_level=None,
    log_file=None,
    log_file_format=None,
    color_enabled=True,
):
    '''
    Configure logging to go to both the console and (syslog or log file). Use the given log levels,
    respectively. If color is enabled, set up log formatting accordingly.

    Raise FileNotFoundError or PermissionError if the log file could not be opened for writing.
    '''
    add_custom_log_levels()

    if syslog_log_level is None:
        syslog_log_level = logging.DISABLED
    if log_file_log_level is None:
        log_file_log_level = console_log_level
    if monitoring_log_level is None:
        monitoring_log_level = console_log_level

    # Log certain log levels to console stderr and others to stdout. This supports use cases like
    # grepping (non-error) output.
    console_disabled = logging.NullHandler()
    console_error_handler = logging.StreamHandler(sys.stderr)
    console_standard_handler = logging.StreamHandler(sys.stdout)
    console_handler = Multi_stream_handler(
        {
            logging.DISABLED: console_disabled,
            logging.CRITICAL: console_error_handler,
            logging.ERROR: console_error_handler,
            logging.WARN: console_error_handler,
            logging.ANSWER: console_standard_handler,
            logging.INFO: console_standard_handler,
            logging.DEBUG: console_standard_handler,
        }
    )

    if color_enabled:
        console_handler.setFormatter(Console_color_formatter())
    else:
        console_handler.setFormatter(Console_no_color_formatter())

    console_handler.setLevel(console_log_level)

    handlers = [console_handler]

    if syslog_log_level != logging.DISABLED:
        syslog_path = None

        if os.path.exists('/dev/log'):
            syslog_path = '/dev/log'
        elif os.path.exists('/var/run/syslog'):
            syslog_path = '/var/run/syslog'
        elif os.path.exists('/var/run/log'):
            syslog_path = '/var/run/log'

        if syslog_path:
            syslog_handler = logging.handlers.SysLogHandler(address=syslog_path)
            syslog_handler.setFormatter(
                logging.Formatter('borgmatic: {levelname} {message}', style='{')  # noqa: FS003
            )
            syslog_handler.setLevel(syslog_log_level)
            handlers.append(syslog_handler)

    if log_file and log_file_log_level != logging.DISABLED:
        file_handler = logging.handlers.WatchedFileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                log_file_format or '[{asctime}] {levelname}: {message}', style='{'  # noqa: FS003
            )
        )
        file_handler.setLevel(log_file_log_level)
        handlers.append(file_handler)

    logging.basicConfig(
        level=min(handler.level for handler in handlers),
        handlers=handlers,
    )
