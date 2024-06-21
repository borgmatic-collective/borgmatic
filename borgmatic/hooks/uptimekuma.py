import logging

import requests

logger = logging.getLogger(__name__)


def initialize_monitor(
    ping_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Uptime Kuma push_code. Use the given configuration filename in any log entries.
    If this is a dry run, then don't actually ping anything.
    '''

    run_states = hook_config.get('states', ['start','finish','fail'])

    if state.name.lower() in run_states:
        
        dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''


        status = "up"
        if state.name.lower() == "fail":
            status = "down"
        
        base_url = hook_config.get('server', 'https://example.uptime.kuma') + "/api/push"
        push_code = hook_config.get('push_code')

        logger.info(f'{config_filename}: Pinging Uptime Kuma push_code {push_code}{dry_run_label}')
        logger.debug(f'{config_filename}: Using Uptime Kuma ping URL {base_url}/{push_code}')
        logger.debug(f'{config_filename}: Full Uptime Kuma state URL {base_url}/{push_code}?status={status}&msg={state.name.lower()}&ping=')

        if not dry_run:
            logging.getLogger('urllib3').setLevel(logging.ERROR)
            try:
                response = requests.get(f'{base_url}/{push_code}?status={status}&msg={state.name.lower()}&ping=')
                if not response.ok:
                    response.raise_for_status()
            except requests.exceptions.RequestException as error:
                logger.warning(f'{config_filename}: Uptime Kuma error: {error}')


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
