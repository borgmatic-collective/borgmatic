from enum import Enum

from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import zabbix as module

SERVER = 'https://zabbix.com/zabbix/api_jsonrpc.php'
ITEMID = 55105
USERNAME = 'testuser'
PASSWORD = 'fakepassword'
API_KEY = 'fakekey'
HOST = 'borg-server'
KEY = 'borg.status'
VALUE = 'fail'

DATA_HOST_KEY = {
    "jsonrpc": "2.0",
    "method": "history.push",
    "params": {"host": HOST, "key": KEY, "value": VALUE},
    "id": 1,
}

DATA_ITEMID = {
    "jsonrpc": "2.0",
    "method": "history.push",
    "params": {"itemid": ITEMID, "value": VALUE},
    "id": 1,
}

DATA_USER_LOGIN = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {"username": USERNAME, "password": PASSWORD},
    "id": 1,
}

AUTH_HEADERS_API_KEY = {
    'Content-Type': 'application/json-rpc',
    'Authorization': f'Bearer {API_KEY}'
}

AUTH_HEADERS_USERNAME_PASSWORD = {
    'Content-Type': 'application/json-rpc'
}

def test_ping_monitor_config_with_api_key_only():
    hook_config = {
        'api_key': API_KEY
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_with_host_only():
    hook_config = {
        'host': HOST
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_with_key_only():
    hook_config = {
        'key': KEY
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_with_server_only():
    hook_config = {
        'server': SERVER
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_user_password_no_zabbix_data():
    hook_config = {
        'server': SERVER,
        'username': USERNAME,
        'password': PASSWORD
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_api_key_no_zabbix_data():
    hook_config = {
        'server': SERVER,
        'api_key': API_KEY
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_itemid_no_auth_data():
    hook_config = {
        'server': SERVER,
        'itemid': ITEMID
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_host_and_key_no_auth_data():
    hook_config = {
        'server': SERVER,
        'host': HOST,
        'key': KEY
    }
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )

def test_ping_monitor_config_host_and_key_with_api_key_auth_data():
    hook_config = {
        'server': SERVER,
        'host': HOST,
        'key': KEY,
        'api_key': API_KEY
    }
    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_API_KEY,
        json=DATA_HOST_KEY,
    ).and_return(flexmock(ok=True)).once()
    flexmock(module.logger).should_receive('warning').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )