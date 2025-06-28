import json
import logging
import os
import platform
import time

import requests

from borgmatic.hooks.monitoring import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_LOKI = {
    monitor.State.START: 'Started',
    monitor.State.FINISH: 'Finished',
    monitor.State.FAIL: 'Failed',
}
TIMEOUT_SECONDS = 10

# Threshold at which logs get flushed to loki
MAX_BUFFER_LINES = 100


class Loki_log_buffer:
    '''
    A log buffer that allows to output the logs as loki requests in json. Allows
    adding labels to the log stream and takes care of communication with loki.
    '''

    def __init__(self, url, dry_run):
        self.url = url
        self.dry_run = dry_run
        self.root = {'streams': [{'stream': {}, 'values': []}]}

    def add_value(self, value):
        '''
        Add a log entry to the stream.
        '''
        timestamp = str(time.time_ns())
        self.root['streams'][0]['values'].append((timestamp, value))

    def add_label(self, label, value):
        '''
        Add a label to the logging stream.
        '''
        self.root['streams'][0]['stream'][label] = value

    def to_request(self):
        return json.dumps(self.root)

    def __len__(self):
        '''
        Gets the number of lines currently in the buffer.
        '''
        return len(self.root['streams'][0]['values'])

    def flush(self):
        if self.dry_run:
            # Just empty the buffer and skip
            self.root['streams'][0]['values'] = []
            logger.info('Skipped uploading logs to loki due to dry run')
            return

        if len(self) == 0:
            # Skip as there are not logs to send yet
            return

        request_body = self.to_request()
        self.root['streams'][0]['values'] = []
        request_header = {'Content-Type': 'application/json'}

        try:
            result = requests.post(
                self.url, headers=request_header, data=request_body, timeout=TIMEOUT_SECONDS
            )
            result.raise_for_status()
        except requests.RequestException:
            logger.warning('Failed to upload logs to loki')


class Loki_log_handler(logging.Handler):
    '''
    A log handler that sends logs to loki.
    '''

    def __init__(self, url, dry_run):
        super().__init__()
        self.buffer = Loki_log_buffer(url, dry_run)

    def emit(self, record):
        '''
        Add a log record from the logging module to the stream.
        '''
        self.raw(record.getMessage())

    def add_label(self, key, value):
        '''
        Add a label to the logging stream.
        '''
        self.buffer.add_label(key, value)

    def raw(self, msg):
        '''
        Add an arbitrary string as a log entry to the stream.
        '''
        self.buffer.add_value(msg)

        if len(self.buffer) > MAX_BUFFER_LINES:
            self.buffer.flush()

    def flush(self):
        '''
        Send the logs to loki and empty the buffer.
        '''
        self.buffer.flush()


def initialize_monitor(hook_config, config, config_filename, monitoring_log_level, dry_run):
    '''
    Add a handler to the root logger to regularly send the logs to loki.
    '''
    url = hook_config.get('url')
    loki = Loki_log_handler(url, dry_run)

    for key, value in hook_config.get('labels').items():
        if value == '__hostname':
            loki.add_label(key, platform.node())
        elif value == '__config':
            loki.add_label(key, os.path.basename(config_filename))
        elif value == '__config_path':
            loki.add_label(key, config_filename)
        else:
            loki.add_label(key, value)

    logging.getLogger().addHandler(loki)


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Add an entry to the loki logger with the current state.
    '''
    for handler in tuple(logging.getLogger().handlers):
        if isinstance(handler, Loki_log_handler):
            if state in MONITOR_STATE_TO_LOKI.keys():
                handler.raw(f'{MONITOR_STATE_TO_LOKI[state]} backup')


def destroy_monitor(hook_config, config, monitoring_log_level, dry_run):
    '''
    Remove the monitor handler that was added to the root logger.
    '''
    logger = logging.getLogger()

    for handler in tuple(logger.handlers):
        if isinstance(handler, Loki_log_handler):
            handler.flush()
            logger.removeHandler(handler)
