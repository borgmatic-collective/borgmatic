import logging

import requests

from borgmatic.hooks import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_HEALTHCHECKS = {
    monitor.State.START: 'start',
    monitor.State.FINISH: None,  # Healthchecks doesn't append to the URL for the finished state.
    monitor.State.FAIL: 'fail',
}

PAYLOAD_TRUNCATION_INDICATOR = '...\n'
PAYLOAD_LIMIT_BYTES = 10 * 1024 - len(PAYLOAD_TRUNCATION_INDICATOR)


class Forgetful_buffering_handler(logging.Handler):
    '''
    A buffering log handler that stores log messages in memory, and throws away messages (oldest
    first) once a particular capacity in bytes is reached.
    '''

    def __init__(self, byte_capacity, log_level):
        super().__init__()

        self.byte_capacity = byte_capacity
        self.byte_count = 0
        self.buffer = []
        self.forgot = False
        self.setLevel(log_level)

    def emit(self, record):
        message = record.getMessage() + '\n'
        self.byte_count += len(message)
        self.buffer.append(message)

        while self.byte_count > self.byte_capacity and self.buffer:
            self.byte_count -= len(self.buffer[0])
            self.buffer.pop(0)
            self.forgot = True


def format_buffered_logs_for_payload():
    '''
    Get the handler previously added to the root logger, and slurp buffered logs out of it to
    send to Healthchecks.
    '''
    try:
        buffering_handler = next(
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, Forgetful_buffering_handler)
        )
    except StopIteration:
        # No handler means no payload.
        return ''

    payload = ''.join(message for message in buffering_handler.buffer)

    if buffering_handler.forgot:
        return PAYLOAD_TRUNCATION_INDICATOR + payload

    return payload


def initialize_monitor(
    ping_url_or_uuid, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    Add a handler to the root logger that stores in memory the most recent logs emitted. That
    way, we can send them all to Healthchecks upon a finish or failure state.
    '''
    logging.getLogger().addHandler(
        Forgetful_buffering_handler(PAYLOAD_LIMIT_BYTES, monitoring_log_level)
    )


def ping_monitor(ping_url_or_uuid, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the given Healthchecks URL or UUID, modified with the monitor.State. Use the given
    configuration filename in any log entries, and log to Healthchecks with the giving log level.
    If this is a dry run, then don't actually ping anything.
    '''
    ping_url = (
        ping_url_or_uuid
        if ping_url_or_uuid.startswith('http')
        else 'https://hc-ping.com/{}'.format(ping_url_or_uuid)
    )
    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

    healthchecks_state = MONITOR_STATE_TO_HEALTHCHECKS.get(state)
    if healthchecks_state:
        ping_url = '{}/{}'.format(ping_url, healthchecks_state)

    logger.info(
        '{}: Pinging Healthchecks {}{}'.format(config_filename, state.name.lower(), dry_run_label)
    )
    logger.debug('{}: Using Healthchecks ping URL {}'.format(config_filename, ping_url))

    if state in (monitor.State.FINISH, monitor.State.FAIL):
        payload = format_buffered_logs_for_payload()
    else:
        payload = ''

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        requests.post(ping_url, data=payload.encode('utf-8'))


def destroy_monitor(ping_url_or_uuid, config_filename, monitoring_log_level, dry_run):
    '''
    Remove the monitor handler that was added to the root logger. This prevents the handler from
    getting reused by other instances of this monitor.
    '''
    logger = logging.getLogger()

    for handler in tuple(logger.handlers):
        if isinstance(handler, Forgetful_buffering_handler):
            logger.removeHandler(handler)
