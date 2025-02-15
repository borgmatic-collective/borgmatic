import datetime
import json
import logging
import platform

import requests

import borgmatic.hooks.credential.parse
from borgmatic.hooks.monitoring import monitor

logger = logging.getLogger(__name__)

EVENTS_API_URL = 'https://events.pagerduty.com/v2/enqueue'


def initialize_monitor(
    integration_key, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    If this is an error state, create a PagerDuty event with the configured integration key. Use
    the given configuration filename in any log entries. If this is a dry run, then don't actually
    create an event.
    '''
    if state != monitor.State.FAIL:
        logger.debug(
            f'Ignoring unsupported monitoring {state.name.lower()} in PagerDuty hook',
        )
        return

    dry_run_label = ' (dry run; not actually sending)' if dry_run else ''
    logger.info(f'Sending failure event to PagerDuty {dry_run_label}')

    if dry_run:
        return

    try:
        integration_key = borgmatic.hooks.credential.parse.resolve_credential(
            hook_config.get('integration_key'), config
        )
    except ValueError as error:
        logger.warning(f'PagerDuty credential error: {error}')
        return

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
                },
            },
        }
    )
    logger.debug(f'Using PagerDuty payload: {payload}')

    logging.getLogger('urllib3').setLevel(logging.ERROR)
    try:
        response = requests.post(EVENTS_API_URL, data=payload.encode('utf-8'))
        if not response.ok:
            response.raise_for_status()
    except requests.exceptions.RequestException as error:
        logger.warning(f'PagerDuty error: {error}')


def destroy_monitor(ping_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
