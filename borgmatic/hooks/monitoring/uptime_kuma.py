import logging

import requests

logger = logging.getLogger(__name__)


TIMEOUT_SECONDS = 10


def initialize_monitor(
    push_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Make a get request to the configured Uptime Kuma push_url. Use the given configuration filename
    in any log entries. If this is a dry run, then don't actually push anything.
    '''
    run_states = hook_config.get('states', ['start', 'finish', 'fail'])

    if state.name.lower() not in run_states:
        return

    dry_run_label = ' (dry run; not actually pushing)' if dry_run else ''
    status = 'down' if state.name.lower() == 'fail' else 'up'
    push_url = hook_config.get('push_url', 'https://example.uptime.kuma/api/push/abcd1234')
    query = f'status={status}&msg={state.name.lower()}'
    logger.info(f'Pushing Uptime Kuma push_url {push_url}?{query} {dry_run_label}')
    logger.debug(f'Full Uptime Kuma state URL {push_url}?{query}')

    if dry_run:
        return

    logging.getLogger('urllib3').setLevel(logging.ERROR)

    try:
        response = requests.get(
            f'{push_url}?{query}',
            verify=hook_config.get('verify_tls', True),
            timeout=TIMEOUT_SECONDS,
        )
        if not response.ok:
            response.raise_for_status()
    except requests.exceptions.RequestException as error:
        logger.warning(f'Uptime Kuma error: {error}')


def destroy_monitor(push_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
