import logging

import requests

from borgmatic.hooks import monitor

logger = logging.getLogger(__name__)

MONITOR_STATE_TO_NTFY = {
    monitor.State.START: None,
    monitor.State.FINISH: None,
    monitor.State.FAIL: None,
}


def initialize_monitor(
    ping_url, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Ping the configured Ntfy topic. Use the given configuration filename in any log entries.
    If this is a dry run, then don't actually ping anything.
    '''

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() in run_states:
        dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

        state_config = hook_config.get(
            state.name.lower(),
            {
                'title': f'A Borgmatic {state.name} event happened',
                'message': f'A Borgmatic {state.name} event happened',
                'priority': 'default',
                'tags': 'borgmatic',
            },
        )

        base_url = hook_config.get('server', 'https://ntfy.sh')
        topic = hook_config.get('topic')

        logger.info(f'{config_filename}: Pinging ntfy topic {topic}{dry_run_label}')
        logger.debug(f'{config_filename}: Using Ntfy ping URL {base_url}/{topic}')

        headers = {
            'X-Title': state_config.get('title'),
            'X-Message': state_config.get('message'),
            'X-Priority': state_config.get('priority'),
            'X-Tags': state_config.get('tags'),
        }

        if not dry_run:
            logging.getLogger('urllib3').setLevel(logging.ERROR)
            try:
                response = requests.post(f'{base_url}/{topic}', headers=headers)
                if not response.ok:
                    response.raise_for_status()
            except requests.exceptions.RequestException as error:
                logger.warning(f'{config_filename}: Ntfy error: {error}')


def destroy_monitor(
    ping_url_or_uuid, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
