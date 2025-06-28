import datetime
import json
import logging
import platform

import requests

import borgmatic.hooks.credential.parse
import borgmatic.hooks.monitoring.logs
from borgmatic.hooks.monitoring import monitor

logger = logging.getLogger(__name__)

EVENTS_API_URL = 'https://events.pagerduty.com/v2/enqueue'
DEFAULT_LOGS_PAYLOAD_LIMIT_BYTES = 10000
HANDLER_IDENTIFIER = 'pagerduty'
TIMEOUT_SECONDS = 10


def initialize_monitor(hook_config, config, config_filename, monitoring_log_level, dry_run):
    '''
    Add a handler to the root logger that stores in memory the most recent logs emitted. That way,
    we can send them all to PagerDuty upon a failure state. But skip this if the "send_logs" option
    is false.
    '''
    if hook_config.get('send_logs') is False:
        return

    ping_body_limit = max(
        DEFAULT_LOGS_PAYLOAD_LIMIT_BYTES
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
    If this is an error state, create a PagerDuty event with the configured integration key. Use
    the given configuration filename in any log entries. If this is a dry run, then don't actually
    create an event.
    '''
    if state != monitor.State.FAIL:
        logger.debug(
            f'Ignoring unsupported monitoring state {state.name.lower()} in PagerDuty hook',
        )
        return

    dry_run_label = ' (dry run; not actually sending)' if dry_run else ''
    logger.info(f'Sending failure event to PagerDuty {dry_run_label}')

    try:
        integration_key = borgmatic.hooks.credential.parse.resolve_credential(
            hook_config.get('integration_key'), config
        )
    except ValueError as error:
        logger.warning(f'PagerDuty credential error: {error}')
        return

    logs_payload = borgmatic.hooks.monitoring.logs.format_buffered_logs_for_payload(
        HANDLER_IDENTIFIER
    )

    hostname = platform.node()
    local_timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()
    payload = json.dumps(
        {
            'routing_key': integration_key,
            'event_action': 'trigger',
            'payload': {
                'summary': f'backup failed on {hostname}',
                'severity': 'error',
                'source': hostname,
                'timestamp': local_timestamp,
                'component': 'borgmatic',
                'group': 'backups',
                'class': 'backup failure',
                'custom_details': {
                    'hostname': hostname,
                    'configuration filename': config_filename,
                    'server time': local_timestamp,
                    'logs': logs_payload,
                },
            },
        }
    )

    if dry_run:
        return

    logging.getLogger('urllib3').setLevel(logging.ERROR)
    try:
        response = requests.post(
            EVENTS_API_URL, data=payload.encode('utf-8'), timeout=TIMEOUT_SECONDS
        )
        if not response.ok:
            response.raise_for_status()
    except requests.exceptions.RequestException as error:
        logger.warning(f'PagerDuty error: {error}')


def destroy_monitor(ping_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    Remove the monitor handler that was added to the root logger. This prevents the handler from
    getting reused by other instances of this monitor.
    '''
    borgmatic.hooks.monitoring.logs.remove_handler(HANDLER_IDENTIFIER)
