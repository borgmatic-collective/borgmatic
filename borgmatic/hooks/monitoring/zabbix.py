import logging

import requests

import borgmatic.hooks.credential.parse

logger = logging.getLogger(__name__)


TIMEOUT_SECONDS = 10


def initialize_monitor(
    ping_url, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No initialization is necessary for this monitor.
    '''
    pass


def send_zabbix_request(server, headers, data):
    '''
    Given a Zabbix server URL, HTTP headers as a dict, and valid Zabbix JSON payload data as a dict,
    send a request to the Zabbix server via API.

    Return the response "result" value or None.
    '''
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    logger.debug(f'Sending a "{data["method"]}" request to the Zabbix server')

    try:
        response = requests.post(server, headers=headers, json=data, timeout=TIMEOUT_SECONDS)

        if not response.ok:
            response.raise_for_status()
    except requests.exceptions.RequestException as error:
        logger.warning(f'Zabbix error: {error}')

        return None

    try:
        result = response.json().get('result')
        error_message = result['data'][0]['error']
    except requests.exceptions.JSONDecodeError:
        logger.warning('Zabbix error: Cannot parse API response')

        return None
    except (TypeError, KeyError, IndexError):
        return result
    else:
        logger.warning(f'Zabbix error: {error_message}')

        return None


def ping_monitor(hook_config, config, config_filename, state, monitoring_log_level, dry_run):
    '''
    Update the configured Zabbix item using either the itemid, or a host and key.
    If this is a dry run, then don't actually update anything.
    '''

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() not in run_states:
        return

    dry_run_label = ' (dry run; not actually updating)' if dry_run else ''

    state_config = hook_config.get(
        state.name.lower(),
        {
            'value': state.name.lower(),
        },
    )

    try:
        username = borgmatic.hooks.credential.parse.resolve_credential(
            hook_config.get('username'), config
        )
        password = borgmatic.hooks.credential.parse.resolve_credential(
            hook_config.get('password'), config
        )
        api_key = borgmatic.hooks.credential.parse.resolve_credential(
            hook_config.get('api_key'), config
        )
    except ValueError as error:
        logger.warning(f'Zabbix credential error: {error}')

        return

    server = hook_config.get('server')
    itemid = hook_config.get('itemid')
    host = hook_config.get('host')
    key = hook_config.get('key')
    value = state_config.get('value')
    headers = {'Content-Type': 'application/json-rpc'}

    logger.info(f'Pinging Zabbix{dry_run_label}')
    logger.debug(f'Using Zabbix URL: {server}')

    # Determine the Zabbix method used to store the value: itemid or host/key
    if itemid is not None:
        logger.info(f'Updating {itemid} on Zabbix')
        data = {
            'jsonrpc': '2.0',
            'method': 'history.push',
            'params': {'itemid': itemid, 'value': value},
            'id': 1,
        }

    elif host is not None and key is not None:
        logger.info(f'Updating Host: "{host}" and Key: "{key}" on Zabbix')
        data = {
            'jsonrpc': '2.0',
            'method': 'history.push',
            'params': {'host': host, 'key': key, 'value': value},
            'id': 1,
        }

    elif host is not None:
        logger.warning('Key missing for Zabbix')

        return
    elif key is not None:
        logger.warning('Host missing for Zabbix')

        return
    else:
        logger.warning('No Zabbix itemid or host/key provided')

        return

    # Determine the authentication method: API key or username/password
    if api_key is not None:
        logger.info('Using API key auth for Zabbix')
        headers['Authorization'] = f'Bearer {api_key}'
    elif username is not None and password is not None:
        logger.info(f'Using user/pass auth with user {username} for Zabbix')
        login_data = {
            'jsonrpc': '2.0',
            'method': 'user.login',
            'params': {'username': username, 'password': password},
            'id': 1,
        }

        if not dry_run:
            result = send_zabbix_request(server, headers, login_data)

            if not result:
                return

            headers['Authorization'] = f'Bearer {result}'
    elif username is not None:
        logger.warning('Password missing for Zabbix authentication')

        return
    elif password is not None:
        logger.warning('Username missing for Zabbix authentication')

        return
    else:
        logger.warning('Authentication data missing for Zabbix')

        return

    if not dry_run:
        send_zabbix_request(server, headers, data)

    if username is not None and password is not None:
        logout_data = {
            'jsonrpc': '2.0',
            'method': 'user.logout',
            'params': [],
            'id': 1,
        }

        if not dry_run:
            send_zabbix_request(server, headers, logout_data)


def destroy_monitor(ping_url_or_uuid, config, monitoring_log_level, dry_run):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
