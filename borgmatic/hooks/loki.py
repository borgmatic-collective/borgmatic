import logging
import requests
import json
import time
import platform
from borgmatic.hooks import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_HEALTHCHECKS = {
    monitor.State.START: 'Started',
    monitor.State.FINISH: 'Finished',
    monitor.State.FAIL: 'Failed',
}

# Threshold at which logs get flushed to loki
MAX_BUFFER_LINES = 100

class loki_log_buffer():
    '''
    A log buffer that allows to output the logs as loki requests in json
    '''
    def __init__(self, url, dry_run):
        self.url = url
        self.dry_run = dry_run
        self.root = {}
        self.root["streams"] = [{}]
        self.root["streams"][0]["stream"] = {}
        self.root["streams"][0]["values"] = []

    def add_value(self, value):
        timestamp = str(time.time_ns())
        self.root["streams"][0]["values"].append((timestamp, value))

    def add_label(self, label, value):
        self.root["streams"][0]["stream"][label] = value

    def _to_request(self):
        return json.dumps(self.root)

    def __len__(self):
        return len(self.root["streams"][0]["values"])

    def flush(self):
        if self.dry_run:
            self.root["streams"][0]["values"] = []
            return
        if len(self) == 0:
            return
        request_body = self._to_request()
        self.root["streams"][0]["values"] = []
        request_header = {"Content-Type": "application/json"}
        try:
            r = requests.post(self.url, headers=request_header, data=request_body, timeout=5)
            r.raise_for_status()
        except requests.RequestException:
            logger.warn("Failed to upload logs to loki")

class loki_log_handeler(logging.Handler):
    '''
    A log handler that sends logs to loki
    '''
    def __init__(self, url, dry_run):
        super().__init__()
        self.buffer = loki_log_buffer(url, dry_run)

    def emit(self, record):
        self.raw(record.getMessage())

    def add_label(self, key, value):
        self.buffer.add_label(key, value)

    def raw(self, msg):
        self.buffer.add_value(msg)
        if len(self.buffer) > MAX_BUFFER_LINES:
            self.buffer.flush()

    def flush(self):
        if len(self.buffer) > 0:
            self.buffer.flush()

def initialize_monitor(hook_config, config, config_filename, monitoring_log_level, dry_run):
    '''
    Add a handler to the root logger to regularly send the logs to loki
    '''
    url = hook_config.get('url')
    loki = loki_log_handeler(url, dry_run)
    for k, v in hook_config.get('labels').items():
        if v == '__hostname':
            loki.add_label(k, platform.node())
        elif v == '__config':
            loki.add_label(k, config_filename.split('/')[-1])
        elif v == '__config_path':
            loki.add_label(k, config_filename)
        else:
            loki.add_label(k, v)
    logging.getLogger().addHandler(loki)

def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Adds an entry to the loki logger with the current state
    '''
    if not dry_run:
        for handler in tuple(logging.getLogger().handlers):
            if isinstance(handler, loki_log_handeler):
                if state in MONITOR_STATE_TO_HEALTHCHECKS.keys():
                    handler.raw(f'{config_filename} {MONITOR_STATE_TO_HEALTHCHECKS[state]} backup')

def destroy_monitor(hook_config, config, config_filename, monitoring_log_level, dry_run):
    '''
    Remove the monitor handler that was added to the root logger.
    '''
    logger = logging.getLogger()
    for handler in tuple(logger.handlers):
        if isinstance(handler, loki_log_handeler):
            handler.flush()
            logger.removeHandler(handler)
