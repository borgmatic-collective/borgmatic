import logging

import requests

from borgmatic.hooks.monitoring import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_CRONITOR = {
    monitor.State.START: 'run',
    monitor.State.FINISH: 'complete',
    monitor.State.FAIL: 'fail',
}


def initialize_monitor(
    ping_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Cronitor URL, modified with the monitor.State. Use the given configuration
    filename in any log entries. If this is a dry run, then don't actually ping anything.
    '''
    if state not in MONITOR_STATE_TO_CRONITOR:
        logger.debug(
            f'{config_filename}: Ignoring unsupported monitoring {state.name.lower()} in Cronitor hook'
        )
        return

    dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''
    ping_url = f"{hook_config['ping_url']}/{MONITOR_STATE_TO_CRONITOR[state]}"

    logger.info(f'{config_filename}: Pinging Cronitor {state.name.lower()}{dry_run_label}')
    logger.debug(f'{config_filename}: Using Cronitor ping URL {ping_url}')

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        try:
            response = requests.get(ping_url)
            if not response.ok:
                response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.warning(f'{config_filename}: Cronitor error: {error}')


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
