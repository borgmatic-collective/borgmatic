from enum import Enum

from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import zabbix as module

server = 'https://zabbix.com/zabbix/api_jsonrpc.php'
itemid = 55105
username = 'testuser'
password = 'fakepassword'
api_key = 'fakekey'
host = 'borg-server'
key = 'borg.status'
value = 'fail'

data_host_key = {
    "jsonrpc": "2.0",
    "method": "history.push",
    "params": {"host": host, "key": key, "value": value},
    "id": 1,
}

data_itemid = {
    "jsonrpc": "2.0",
    "method": "history.push",
    "params": {"itemid": itemid, "value": value},
    "id": 1,
}

data_user_login = {
    "jsonrpc": "2.0",
    "method": "user.login",
    "params": {"username": username, "password": password},
    "id": 1,
}

auth_headers_api_key = {
    'Content-Type': 'application/json-rpc',
    'Authorization': f'Bearer {api_key}'
}

auth_headers_username_password = {
    'Content-Type': 'application/json-rpc'
}

def test_ping_monitor_config_with_api_key_only():
    hook_config = {
        'api_key': api_key
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
        'host': host
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
        'key': key
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
        'server': server
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
        'server': server,
        'username': username,
        'password': password
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
        'server': server,
        'api_key': api_key
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
        'server': server,
        'itemid': itemid
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
        'server': server,
        'host': host,
        'key': key
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
        'server': server,
        'host': host,
        'key': key,
        'api_key': api_key
    }
    flexmock(module.requests).should_receive('post').with_args(
        f'{server}',
        headers=auth_headers_api_key,
        json=data_host_key,
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