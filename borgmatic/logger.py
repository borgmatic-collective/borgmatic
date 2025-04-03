import enum
import logging
import logging.handlers
import os
import sys


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


def should_do_markup(configs, json_enabled):
    '''
    Given a dict of configuration filename to corresponding parsed configuration (which already have
    any command-line overrides applied) and whether json is enabled, determine if we should enable
    color marking up.
    '''
    if json_enabled:
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


class Log_prefix_formatter(logging.Formatter):
    def __init__(self, fmt='{prefix}{message}', style='{', *args, **kwargs):  # pragma: no cover
        self.prefix = None

        super(Log_prefix_formatter, self).__init__(fmt=fmt, style=style, *args, **kwargs)

    def format(self, record):  # pragma: no cover
        record.prefix = f'{self.prefix}: ' if self.prefix else ''

        return super(Log_prefix_formatter, self).format(record)


class Color(enum.Enum):
    RESET = 0
    RED = 31
    GREEN = 32
    YELLOW = 33
    MAGENTA = 35
    CYAN = 36


class Console_color_formatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.prefix = None
        super(Console_color_formatter, self).__init__(
            '{prefix}{message}', style='{', *args, **kwargs
        )

    def format(self, record):
        add_custom_log_levels()

        color = (
            {
                logging.CRITICAL: Color.RED,
                logging.ERROR: Color.RED,
                logging.WARN: Color.YELLOW,
                logging.ANSWER: Color.MAGENTA,
                logging.INFO: Color.GREEN,
                logging.DEBUG: Color.CYAN,
            }
            .get(record.levelno)
            .value
        )
        record.prefix = f'{self.prefix}: ' if self.prefix else ''

        return color_text(color, super(Console_color_formatter, self).format(record))


def ansi_escape_code(color):  # pragma: no cover
    '''
    Given a color value, produce the corresponding ANSI escape code.
    '''
    return f'\x1b[{color}m'


def color_text(color, message):
    '''
    Given a color value and a message, return the message colored with ANSI escape codes.
    '''
    if not color:
        return message

    return f'{ansi_escape_code(color)}{message}{ansi_escape_code(Color.RESET.value)}'


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


def get_log_prefix():
    '''
    Return the current log prefix set by set_log_prefix(). Return None if no such prefix exists.

    It would be a whole lot easier to use logger.Formatter(defaults=...) instead, but that argument
    doesn't exist until Python 3.10+.
    '''
    try:
        formatter = next(
            handler.formatter
            for handler in logging.getLogger().handlers
            if handler.formatter
            if hasattr(handler.formatter, 'prefix')
        )
    except StopIteration:
        return None

    return formatter.prefix


def set_log_prefix(prefix):
    '''
    Given a log prefix as a string, set it into the each handler's formatter so that it can inject
    the prefix into each logged record.
    '''
    for handler in logging.getLogger().handlers:
        if handler.formatter and hasattr(handler.formatter, 'prefix'):
            handler.formatter.prefix = prefix


class Log_prefix:
    '''
    A Python context manager for setting a log prefix so that it shows up in every subsequent
    logging message for the duration of the context manager. For this to work, it relies on each
    logging formatter to be initialized with "{prefix}" somewhere in its logging format.

    Example use as a context manager:


       with borgmatic.logger.Log_prefix('myprefix'):
            do_something_that_logs()

    For the scope of that "with" statement, any logs created are prefixed with "myprefix: ".
    Afterwards, the prefix gets restored to whatever it was prior to the context manager.
    '''

    def __init__(self, prefix):
        '''
        Given the desired log prefix, save it for use below. Set prefix to None to disable any
        prefix from getting logged.
        '''
        self.prefix = prefix
        self.original_prefix = None

    def __enter__(self):
        '''
        Set the prefix onto the formatter defaults for every logging handler so that the prefix ends
        up in every log message. But first, save off any original prefix so that it can be restored
        below.
        '''
        self.original_prefix = get_log_prefix()
        set_log_prefix(self.prefix)

    def __exit__(self, exception_type, exception, traceback):
        '''
        Restore any original prefix.
        '''
        set_log_prefix(self.original_prefix)


class Delayed_logging_handler(logging.handlers.BufferingHandler):
    '''
    A logging handler that buffers logs and doesn't flush them until explicitly flushed (after
    target handlers are actually set). It's useful for holding onto messages logged before logging
    is configured, ensuring those records eventually make their way to the relevant logging
    handlers.

    When flushing, don't forward log records to a target handler if the record's log level is below
    that of the handler. This recreates the standard logging behavior of, say, logging.DEBUG records
    getting suppressed if a handler's level is only set to logging.INFO.
    '''

    def __init__(self):
        super(Delayed_logging_handler, self).__init__(capacity=0)

        self.targets = None

    def shouldFlush(self, record):
        return self.targets is not None

    def flush(self):
        self.acquire()

        try:
            if not self.targets:
                return

            for record in self.buffer:
                for target in self.targets:
                    if record.levelno >= target.level:
                        target.handle(record)

            self.buffer.clear()
        finally:
            self.release()


def configure_delayed_logging():  # pragma: no cover
    '''
    Configure a delayed logging handler to buffer anything that gets logged until we're ready to
    deal with it.
    '''
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[Delayed_logging_handler()],
    )


def flush_delayed_logging(target_handlers):
    '''
    Flush any previously buffered logs to our "real" logging handlers.
    '''
    root_logger = logging.getLogger()

    if root_logger.handlers and isinstance(root_logger.handlers[0], Delayed_logging_handler):
        delayed_handler = root_logger.handlers[0]
        delayed_handler.targets = target_handlers
        delayed_handler.flush()
        root_logger.removeHandler(delayed_handler)


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
        console_handler.setFormatter(Log_prefix_formatter())

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
                Log_prefix_formatter(
                    'borgmatic: {levelname} {prefix}{message}',  # noqa: FS003
                )
            )
            syslog_handler.setLevel(syslog_log_level)
            handlers.append(syslog_handler)

    if log_file and log_file_log_level != logging.DISABLED:
        file_handler = logging.handlers.WatchedFileHandler(log_file)
        file_handler.setFormatter(
            Log_prefix_formatter(
                log_file_format or '[{asctime}] {levelname}: {prefix}{message}',  # noqa: FS003
            )
        )
        file_handler.setLevel(log_file_log_level)
        handlers.append(file_handler)

    flush_delayed_logging(handlers)

    logging.basicConfig(
        level=min(handler.level for handler in handlers),
        handlers=handlers,
    )
