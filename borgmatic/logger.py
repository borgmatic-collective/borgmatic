import enum
import json
import logging
import logging.handlers
import os
import socket
import sys


def to_bool(arg):
    '''
    Return a boolean value based on `arg`.
    '''
    if arg is None or isinstance(arg, bool):
        return arg

    if isinstance(arg, str):
        arg = arg.lower()

    return arg in {'yes', 'on', '1', 'true', 1}


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
        super().__init__()
        self.log_level_to_handler = log_level_to_stream_handler
        self.handlers = set(self.log_level_to_handler.values())

    def flush(self):  # pragma: no cover
        super().flush()

        for handler in self.handlers:
            handler.flush()

    def emit(self, record):
        '''
        Dispatch the log record to the appropriate stream handler for the record's log level.
        '''
        self.log_level_to_handler[record.levelno].emit(record)

    def setFormatter(self, formatter):  # pragma: no cover  # noqa: N802
        super().setFormatter(formatter)

        for handler in self.handlers:
            handler.setFormatter(formatter)

    def setLevel(self, level):  # pragma: no cover  # noqa: N802
        super().setLevel(level)

        for handler in self.handlers:
            handler.setLevel(level)


DEFAULT_JOURNALD_PRIORITY = 6


class JournaldHandler(logging.Handler):
    def __init__(self, journald_socket_path):
        super().__init__()

        add_custom_log_levels()

        self.journald_socket_path = journald_socket_path
        self.log_level_to_journald_priority = {
            logging.ERROR: 3,
            logging.WARNING: 4,
            logging.ANSWER: 5,
            logging.INFO: 6,
            logging.DEBUG: 7,
        }

    def emit(self, record):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        try:
            message_parts = []
            entry = dict(
                LOGGER_NAME=record.name,
                MESSAGE=record.getMessage(),
                PRIORITY=self.log_level_to_journald_priority.get(record.levelno, DEFAULT_JOURNALD_PRIORITY),
                SYSLOG_IDENTIFIER='borgmatic',
                SYSLOG_PID=os.getpid(),
                UNIT=record.name,
            )

            for key, value in entry.items():
                key = key.upper().encode('utf-8')
                value = str(value).encode('utf-8')

                # Multi-line and single-line values use different formats on the wire.
                if b'\n' in value:
                    message_parts.extend((key, b'\n'))
                    message_parts.extend((len(value).to_bytes(8, 'little'), value, b'\n'))
                else:
                    message_parts.extend((key, b'=', value, b'\n'))

            sock.sendto(b''.join(message_parts), self.journald_socket_path)
        finally:
            sock.close()


class Log_prefix_formatter(logging.Formatter):
    def __init__(self, fmt='{prefix}{message}', *args, style='{', **kwargs):
        self.prefix = None

        super().__init__(*args, fmt=fmt, style=style, **kwargs)

    def format(self, record):  # pragma: no cover
        record.prefix = f'{self.prefix}: ' if self.prefix else ''

        return super().format(record)


def log_record_to_json(record, **extra):
    '''
    Given a logging.LogRecord, return it as a JSON-encoded string containing relevant attributes.
    Add in any extra kwargs that are given.
    '''
    return json.dumps(
        dict(
            type='log_message',
            time=record.created,
            message=record.getMessage(),
            levelname=record.levelname,
            name=record.name,
            **extra,
        )
    )


class Json_formatter(logging.Formatter):
    def __init__(self, fmt='{message}', *args, style='{', **kwargs):
        super().__init__(*args, fmt=fmt, style=style, **kwargs)

    def format(self, record):
        return log_record_to_json(record)


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
        super().__init__(
            '{prefix}{message}',
            *args,
            style='{',
            **kwargs,
        )

    def format(self, record):
        add_custom_log_levels()

        color = {
            logging.CRITICAL: Color.RED,
            logging.ERROR: Color.RED,
            logging.WARNING: Color.YELLOW,
            logging.ANSWER: Color.MAGENTA,
            logging.INFO: Color.GREEN,
            logging.DEBUG: Color.CYAN,
        }.get(record.levelno).value
        record.prefix = f'{self.prefix}: ' if self.prefix else ''

        return color_text(color, super().format(record))


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
            logging.log(level_number, message, *args, **kwargs)  # noqa: LOG015

        setattr(logging, method_name, log_to_root)


ANSWER = logging.WARNING - 5
DISABLED = logging.CRITICAL + 10


def add_custom_log_levels():  # pragma: no cover
    '''
    Add a custom log level between WARNING and INFO for user-requested answers.
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
        super().__init__(capacity=0)

        self.targets = None

    def shouldFlush(self, record):  # noqa: N802
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


JOURNALD_SOCKET_PATH = '/run/systemd/journal/socket'
SYSLOG_PATHS = ('/dev/log', '/var/run/syslog', '/var/run/log')


def configure_logging(
    console_log_level,
    syslog_log_level=None,
    log_file_log_level=None,
    monitoring_log_level=None,
    log_file=None,
    log_file_format=None,
    log_json=False,
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
            logging.WARNING: console_error_handler,
            logging.ANSWER: console_standard_handler,
            logging.INFO: console_standard_handler,
            logging.DEBUG: console_standard_handler,
        },
    )

    if log_json:
        console_handler.setFormatter(Json_formatter())
    elif color_enabled:
        console_handler.setFormatter(Console_color_formatter())
    else:
        console_handler.setFormatter(Log_prefix_formatter())

    console_handler.setLevel(console_log_level)
    handlers = [console_handler]

    if syslog_log_level != logging.DISABLED:
        if os.path.exists(JOURNALD_SOCKET_PATH):
            journald_handler = JournaldHandler(JOURNALD_SOCKET_PATH)
            journald_handler.setLevel(syslog_log_level)
            handlers.append(journald_handler)
        else:
            syslog_path = next(
                (
                    path
                    for path in SYSLOG_PATHS
                    if os.path.exists(path)
                ),
                None,
            )

            if syslog_path:
                syslog_handler = logging.handlers.SysLogHandler(address=syslog_path)
                syslog_handler.setFormatter(
                    Log_prefix_formatter(
                        'borgmatic: {levelname} {prefix}{message}',
                    ),
                )
                syslog_handler.setLevel(syslog_log_level)
                handlers.append(syslog_handler)

    if log_file and log_file_log_level != logging.DISABLED:
        file_handler = logging.handlers.WatchedFileHandler(log_file)
        file_handler.setFormatter(
            Json_formatter() if log_json else
            Log_prefix_formatter(
                log_file_format or '[{asctime}] {levelname}: {prefix}{message}',
            ),
        )
        file_handler.setLevel(log_file_log_level)
        handlers.append(file_handler)

    flush_delayed_logging(handlers)

    logging.basicConfig(
        level=min(handler.level for handler in handlers),
        handlers=handlers,
    )
