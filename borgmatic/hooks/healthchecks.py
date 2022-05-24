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
DEFAULT_PING_BODY_LIMIT_BYTES = 100000


class Forgetful_buffering_handler(logging.Handler):
    '''
    A buffering log handler that stores log messages in memory, and throws away messages (oldest
    first) once a particular capacity in bytes is reached. But if the given byte capacity is zero,
    don't throw away any messages.
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

        if not self.byte_capacity:
            return

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


def initialize_monitor(hook_config, config_filename, monitoring_log_level, dry_run):
    '''
    Add a handler to the root logger that stores in memory the most recent logs emitted. That way,
    we can send them all to Healthchecks upon a finish or failure state. But skip this if the
    "send_logs" option is false.
    '''
    if hook_config.get('send_logs') is False:
        return

    ping_body_limit = max(
        hook_config.get('ping_body_limit', DEFAULT_PING_BODY_LIMIT_BYTES)
        - len(PAYLOAD_TRUNCATION_INDICATOR),
        0,
    )

    logging.getLogger().addHandler(
        Forgetful_buffering_handler(ping_body_limit, monitoring_log_level)
    )


def ping_monitor(hook_config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Healthchecks URL or UUID, modified with the monitor.State. Use the given
    configuration filename in any log entries, and log to Healthchecks with the giving log level.
    If this is a dry run, then don't actually ping anything.
    '''
    ping_url = (
        hook_config['ping_url']
        if hook_config['ping_url'].startswith('http')
        else 'https://hc-ping.com/{}'.format(hook_config['ping_url'])
    )
    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

    if 'states' in hook_config and state.name.lower() not in hook_config['states']:
        logger.info(
            f'{config_filename}: Skipping Healthchecks {state.name.lower()} ping due to configured states'
        )
        return

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
        try:
            requests.post(ping_url, data=payload.encode('utf-8'))
        except requests.exceptions.RequestException as error:
            logger.warning(f'{config_filename}: Healthchecks error: {error}')


def destroy_monitor(hook_config, config_filename, monitoring_log_level, dry_run):
    '''
    Remove the monitor handler that was added to the root logger. This prevents the handler from
    getting reused by other instances of this monitor.
    '''
    logger = logging.getLogger()

    for handler in tuple(logger.handlers):
        if isinstance(handler, Forgetful_buffering_handler):
            logger.removeHandler(handler)
