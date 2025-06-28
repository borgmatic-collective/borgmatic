import logging

import requests

import borgmatic.hooks.credential.parse

logger = logging.getLogger(__name__)


EMERGENCY_PRIORITY = 2
TIMEOUT_SECONDS = 10


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

    try:
        token = borgmatic.hooks.credential.parse.resolve_credential(
            hook_config.get('token'), config
        )
        user = borgmatic.hooks.credential.parse.resolve_credential(hook_config.get('user'), config)
    except ValueError as error:
        logger.warning(f'Pushover credential error: {error}')
        return

    logger.info(f'Updating Pushover{dry_run_label}')

    if state_config.get('priority') == EMERGENCY_PRIORITY:
        if 'expire' not in state_config:
            logger.info('Setting expire to default (10 min)')
            state_config['expire'] = 600
        if 'retry' not in state_config:
            logger.info('Setting retry to default (30 sec)')
            state_config['retry'] = 30
    else:
        if 'expire' in state_config or 'retry' in state_config:
            raise ValueError(
                'The configuration parameters retry and expire should not be set when priority is not equal to 2. Please remove them from the configuration.'
            )

    state_config = {
        key: (int(value) if key == 'html' else value) for key, value in state_config.items()
    }

    data = dict(
        {
            'token': token,
            'user': user,
            # Default to state name. Can be overwritten by state_config below.
            'message': state.name.lower(),
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
                timeout=TIMEOUT_SECONDS,
            )
            if not response.ok:
                response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.warning(f'Pushover error: {error}')


def destroy_monitor(ping_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
