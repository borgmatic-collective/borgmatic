import logging

import requests

from borgmatic.hooks.monitoring import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_CRONHUB = {
    monitor.State.START: 'start',
    monitor.State.FINISH: 'finish',
    monitor.State.FAIL: 'fail',
}
TIMEOUT_SECONDS = 10


def initialize_monitor(
    ping_url,
    config,
    config_filename,
    monitoring_log_level,
    dry_run,
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Cronhub URL, modified with the monitor.State. Use the given configuration
    filename in any log entries. If this is a dry run, then don't actually ping anything.
    '''
    if state not in MONITOR_STATE_TO_CRONHUB:
        logger.debug(f'Ignoring unsupported monitoring state {state.name.lower()} in Cronhub hook')
        return

    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''
    formatted_state = f'/{MONITOR_STATE_TO_CRONHUB[state]}/'
    ping_url = (
        hook_config['ping_url']
        .replace('/start/', formatted_state)
        .replace('/ping/', formatted_state)
    )

    logger.info(f'Pinging Cronhub {state.name.lower()}{dry_run_label}')
    logger.debug(f'Using Cronhub ping URL {ping_url}')

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        try:
            response = requests.get(ping_url, timeout=TIMEOUT_SECONDS)
            if not response.ok:
                response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.warning(f'Cronhub error: {error}')


def destroy_monitor(ping_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
