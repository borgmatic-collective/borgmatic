import logging

import requests

logger = logging.getLogger(__name__)


EMERGENCY_PRIORITY = 2


def initialize_monitor(
    ping_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Post a message to the configured Pushover application.
    If this is a dry run, then don't actually update anything.
    '''

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() not in run_states:
        return

    dry_run_label = ' (dry run; not actually updating)' if dry_run else ''

    state_config = hook_config.get(state.name.lower(), {})

    token = hook_config.get('token')
    user = hook_config.get('user')

    logger.info(f'{config_filename}: Updating Pushover{dry_run_label}')

    if state_config.get('priority') == EMERGENCY_PRIORITY:
        if 'expire' not in state_config:
            logger.info(f'{config_filename}: Setting expire to default (10min).')
            state_config['expire'] = 600
        if 'retry' not in state_config:
            logger.info(f'{config_filename}: Setting retry to default (30sec).')
            state_config['retry'] = 30
    else:
        state_config.pop('expire', None)
        state_config.pop('retry', None)

    state_config = {
        key: (1 if value is True and key in 'html' else value)
        for key, value in state_config.items()
    }

    data = dict(
        {
            'token': token,
            'user': user,
            'message': state.name.lower(),  # default to state name. Can be overwritten in state_config loop below.
        },
        **state_config,
    )

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        try:
            response = requests.post(
                'https://api.pushover.net/1/messages.json',
                headers={'Content-type': 'application/x-www-form-urlencoded'},
                data=data,
            )
            if not response.ok:
                response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.warning(f'{config_filename}: Pushover error: {error}')


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
