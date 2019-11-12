import logging

import requests

from borgmatic.hooks import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_HEALTHCHECKS = {
    monitor.State.START: 'start',
    monitor.State.FINISH: None,  # Healthchecks doesn't append to the URL for the finished state.
    monitor.State.FAIL: 'fail',
}


def ping_monitor(ping_url_or_uuid, config_filename, state, dry_run):
    '''
    Ping the given Healthchecks URL or UUID, modified with the monitor.State. Use the given
    configuration filename in any log entries. If this is a dry run, then don't actually ping
    anything.
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

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        requests.get(ping_url)
