import logging
import requests
import json

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
    Update the configured Zabbix item using either the itemid, or a host and key.
    If this is a dry run, then don't actually update anything.
    '''

    run_states = hook_config.get('states', ['fail'])

    if state.name.lower() not in run_states:
        return

    dry_run_label = ' (dry run; not actually updating)' if dry_run else ''

    state_config = hook_config.get(state.name.lower(),{'value': f'invalid',},)

    base_url = hook_config.get('server', 'https://cloud.zabbix.com/zabbix/api_jsonrpc.php')
    username = hook_config.get('username')
    password = hook_config.get('password')
    api_key = hook_config.get('api_key')
    itemid = hook_config.get('itemid')
    host = hook_config.get('host')
    key = hook_config.get('key')
    value = state_config.get('value')
    headers = {'Content-Type': 'application/json-rpc'}

    logger.info(f'{config_filename}: Updating Zabbix {dry_run_label}')
    logger.debug(f'{config_filename}: Using Zabbix URL: {base_url}')

    # Determine the zabbix method used to store the value: itemid or host/key
    if itemid is not None:
        logger.info(f'{config_filename}: Updating {itemid} on Zabbix')
        data = {"jsonrpc":"2.0","method":"history.push","params":{"itemid":itemid,"value":value},"id":1}
    
    elif host and key is not None:
        logger.info(f'{config_filename}: Updating Host:{host} and Key:{key} on Zabbix')
        data = {"jsonrpc":"2.0","method":"history.push","params":{"host":host,"key":key,"value":value},"id":1}

    elif host is not None:
        logger.warning( f'{config_filename}: Key missing for Zabbix authentication' )
        return

    elif key is not None:
        logger.warning( f'{config_filename}: Host missing for Zabbix authentication' )
        return

    # Determine the authentication method: API key or username/password
    if api_key is not None:
        logger.info(f'{config_filename}: Using API key auth for Zabbix')
        headers['Authorization'] = 'Bearer ' + api_key
        
    elif username and password is not None:
        logger.info(f'{config_filename}: Using user/pass auth with user {username} for Zabbix')
        response = requests.post(base_url, headers=headers, data='{"jsonrpc":"2.0","method":"user.login","params":{"username":"'+username+'","password":"'+password+'"},"id":1}')
        data['auth'] = response.json().get('result')

    elif username is not None:
        logger.warning( f'{config_filename}: Password missing for Zabbix authentication' )
        return

    elif password is not None:
        logger.warning( f'{config_filename}: Username missing for Zabbix authentication' )
        return

    if not dry_run:
        logging.getLogger('urllib3').setLevel(logging.ERROR)
        try:
            response = requests.post(base_url, headers=headers, data=json.dumps(data))
            if not response.ok:
                response.raise_for_status()
        except requests.exceptions.RequestException as error:
            logger.warning(f'{config_filename}: Zabbix error: {error}')


def destroy_monitor(
    ping_url_or_uuid, config, config_filename, monitoring_log_level, dry_run
):  # pragma: no cover
    '''
    No destruction is necessary for this monitor.
    '''
    pass
