import contextlib
import logging

import textual._context
import textual.widgets
import textual.worker

import borgmatic.logger


class Rich_color_formatter(logging.Formatter):
    '''
    A Python logging formatter that formats log records with Rich-compatible color markup according
    to their levels.
    '''

    def __init__(self, *args, **kwargs):
        self.prefix = None
        super().__init__(
            '{prefix}{message}',
            *args,
            style='{',
            **kwargs,
        )

    def format(self, record):
        '''
        Given a log record, format it with Rich-compatibe color markup corresponding to its log
        level.
        '''
        borgmatic.logger.add_custom_log_levels()

        color = {
            logging.CRITICAL: 'bright_red',
            logging.ERROR: 'bright_red',
            logging.WARNING: 'bright_yellow',
            logging.ANSWER: 'bright_magenta',
            logging.INFO: 'bright_green',
            logging.DEBUG: 'bright_cyan',
        }.get(record.levelno)
        record.prefix = f'{self.prefix}: ' if self.prefix else ''

        return f'[{color}]{super().format(record)}[/{color}]'


class Browse_log_handler(logging.Handler):
    '''
    A Python log handler that writes any log records to a logging widget.
    '''

    def __init__(self, logs_widget):
        '''
        Given a logs widget, save it for use below.
        '''
        self.logs_widget = logs_widget

        super().__init__()

    def emit(self, record):
        '''
        Given a log record, format it and log it to the logs widgets. This works whether or not the
        logging is happening in the main thread.
        '''
        message = self.format(record)

        try:
            textual.worker.get_current_worker()
            self.logs_widget.app.call_from_thread(self.logs_widget.write, message)
        except (RuntimeError, textual.worker.NoActiveWorker):
            with contextlib.suppress(textual._context.NoActiveAppError):
                self.logs_widget.write(message)


def log_to_widget(logs_widget):
    '''
    Given a Textual RichLog logs widget, add a log handler and formatter that logs to it. Also
    remove the default borgmatic console log handler so it doesn't try to log all over our UI.
    '''
    handler = Browse_log_handler(logs_widget)
    handler.setFormatter(Rich_color_formatter())
    logger = logging.getLogger()
    logger.setLevel(min(handler.level for handler in logger.handlers))
    logger.addHandler(handler)

    with contextlib.suppress(StopIteration):
        console_handler = next(
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, borgmatic.logger.Multi_stream_handler)
        )
        logger.removeHandler(console_handler)


class Logs(textual.widgets.RichLog):
    '''
    A widget for viewing borgmatic logs in realtime. The log level is determined by borgmatic's
    current verbosity level.
    '''

    def __init__(self):
        super().__init__(markup=True, id='logs', classes='panel')
        self.border_title = '🪵 logs'
