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
    Ping the configured Ntfy topic. Use the given configuration filename in any log entries.
    If this is a dry run, then don't actually ping anything.
    '''

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() in run_states:
        dry_run_label = ' (dry run; not actually pinging)' if dry_run else ''

        state_config = hook_config.get(
            state.name.lower(),
            {
                'title': f'A borgmatic {state.name} event happened',
                'message': f'A borgmatic {state.name} event happened',
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

        username = hook_config.get('username')
        password = hook_config.get('password')
        access_token = hook_config.get('access_token')
        auth = None

        if access_token is not None:
            if username or password:
                logger.warning(
                    f'{config_filename}: ntfy access_token is set but so is username/password, only using access_token'
                )
            auth = requests.auth.HTTPBasicAuth('', access_token)
        elif (username and password) is not None:
            auth = requests.auth.HTTPBasicAuth(username, password)
            logger.info(f'{config_filename}: Using basic auth with user {username} for ntfy')
        elif username is not None:
            logger.warning(
                f'{config_filename}: Password missing for ntfy authentication, defaulting to no auth'
            )
        elif password is not None:
            logger.warning(
                f'{config_filename}: Username missing for ntfy authentication, defaulting to no auth'
            )

        if not dry_run:
            logging.getLogger('urllib3').setLevel(logging.ERROR)
            try:
                response = requests.post(f'{base_url}/{topic}', headers=headers, auth=auth)
                if not response.ok:
                    response.raise_for_status()
            except requests.exceptions.RequestException as error:
                logger.warning(f'{config_filename}: ntfy error: {error}')


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
