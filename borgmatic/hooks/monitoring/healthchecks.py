import logging
import re

import requests

import borgmatic.hooks.monitoring.logs
from borgmatic.hooks.monitoring import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_HEALTHCHECKS = {
    monitor.State.START: 'start',
    monitor.State.FINISH: None,  # Healthchecks doesn't append to the URL for the finished state.
    monitor.State.FAIL: 'fail',
    monitor.State.LOG: 'log',
}

DEFAULT_PING_BODY_LIMIT_BYTES = 100000
HANDLER_IDENTIFIER = 'healthchecks'
TIMEOUT_SECONDS = 10


def initialize_monitor(hook_config, config, config_filename, monitoring_log_level, dry_run):
    '''
    Add a handler to the root logger that stores in memory the most recent logs emitted. That way,
    we can send them all to Healthchecks upon a finish or failure state. But skip this if the
    "send_logs" option is false.
    '''
    if hook_config.get('send_logs') is False:
        return

    ping_body_limit = max(
        hook_config.get('ping_body_limit', DEFAULT_PING_BODY_LIMIT_BYTES)
        - len(borgmatic.hooks.monitoring.logs.PAYLOAD_TRUNCATION_INDICATOR),
        0,
    )

    borgmatic.hooks.monitoring.logs.add_handler(
        borgmatic.hooks.monitoring.logs.Forgetful_buffering_handler(
            HANDLER_IDENTIFIER, ping_body_limit, monitoring_log_level
        )
    )


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Healthchecks URL or UUID, modified with the monitor.State. Use the given
    configuration filename in any log entries, and log to Healthchecks with the giving log level.
    If this is a dry run, then don't actually ping anything.
    '''
    ping_url = (
        hook_config['ping_url']
        if hook_config['ping_url'].startswith('http')
        else f"https://hc-ping.com/{hook_config['ping_url']}"
    )
    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

    if 'states' in hook_config and state.name.lower() not in hook_config['states']:
        logger.info(f'Skipping Healthchecks {state.name.lower()} ping due to configured states')
        return

    ping_url_is_uuid = re.search(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', ping_url)

    healthchecks_state = MONITOR_STATE_TO_HEALTHCHECKS.get(state)
    if healthchecks_state:
        ping_url = f'{ping_url}/{healthchecks_state}'

    if hook_config.get('create_slug'):
        if ping_url_is_uuid:
            logger.warning('Healthchecks UUIDs do not support auto provisionning; ignoring')
        else:
            ping_url = f'{ping_url}?create=1'

    logger.info(f'Pinging Healthchecks {state.name.lower()}{dry_run_label}')
    logger.debug(f'Using Healthchecks ping URL {ping_url}')

    if state in (monitor.State.FINISH, monitor.State.FAIL, monitor.State.LOG):
        payload = borgmatic.hooks.monitoring.logs.format_buffered_logs_for_payload(
            HANDLER_IDENTIFIER
        )
    else:
        payload = ''

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        try:
            response = requests.post(
                ping_url,
                data=payload.encode('utf-8'),
                verify=hook_config.get('verify_tls', True),
                timeout=TIMEOUT_SECONDS,
            )
            if not response.ok:
                response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.warning(f'Healthchecks error: {error}')


def destroy_monitor(hook_config, config, monitoring_log_level, dry_run):
    '''
    Remove the monitor handler that was added to the root logger. This prevents the handler from
    getting reused by other instances of this monitor.
    '''
    borgmatic.hooks.monitoring.logs.remove_handler(HANDLER_IDENTIFIER)
