from flexmock import flexmock

import borgmatic.hooks.monitoring.monitor
from borgmatic.hooks.monitoring import zabbix as module

SERVER = 'https://zabbix.com/zabbix/api_jsonrpc.php'
ITEMID = 55105
USERNAME = 'testuser'
PASSWORD = 'fakepassword'
API_KEY = 'fakekey'
HOST = 'borg-server'
KEY = 'borg.status'
VALUE = 'fail'

DATA_HOST_KEY = {
    'jsonrpc': '2.0',
    'method': 'history.push',
    'params': {'host': HOST, 'key': KEY, 'value': VALUE},
    'id': 1,
}

DATA_HOST_KEY_WITH_KEY_VALUE = {
    'jsonrpc': '2.0',
    'method': 'history.push',
    'params': {'host': HOST, 'key': KEY, 'value': VALUE},
    'id': 1,
    'auth': '3fe6ed01a69ebd79907a120bcd04e494',
}

DATA_ITEMID = {
    'jsonrpc': '2.0',
    'method': 'history.push',
    'params': {'itemid': ITEMID, 'value': VALUE},
    'id': 1,
}

DATA_HOST_KEY_WITH_ITEMID = {
    'jsonrpc': '2.0',
    'method': 'history.push',
    'params': {'itemid': ITEMID, 'value': VALUE},
    'id': 1,
    'auth': '3fe6ed01a69ebd79907a120bcd04e494',
}

DATA_USER_LOGIN = {
    'jsonrpc': '2.0',
    'method': 'user.login',
    'params': {'username': USERNAME, 'password': PASSWORD},
    'id': 1,
}

AUTH_HEADERS_API_KEY = {
    'Content-Type': 'application/json-rpc',
    'Authorization': f'Bearer {API_KEY}',
}

AUTH_HEADERS_USERNAME_PASSWORD = {'Content-Type': 'application/json-rpc'}


def test_ping_monitor_with_non_matching_state_bails():
    hook_config = {'api_key': API_KEY}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_api_key_only_bails():
    # This test should exit early since only providing an API KEY is not enough
    # for the hook to work
    hook_config = {'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_host_only_bails():
    # This test should exit early since only providing a HOST is not enough
    # for the hook to work
    hook_config = {'host': HOST}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_key_only_bails():
    # This test should exit early since only providing a KEY is not enough
    # for the hook to work
    hook_config = {'key': KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_server_only_bails():
    # This test should exit early since only providing a SERVER is not enough
    # for the hook to work
    hook_config = {'server': SERVER}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_user_password_no_zabbix_data_bails():
    # This test should exit early since there are HOST/KEY or ITEMID provided to publish data to
    hook_config = {'server': SERVER, 'username': USERNAME, 'password': PASSWORD}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_api_key_no_zabbix_data_bails():
    # This test should exit early since there are HOST/KEY or ITEMID provided to publish data to
    hook_config = {'server': SERVER, 'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_itemid_no_auth_data_bails():
    # This test should exit early since there is no authentication provided
    # and Zabbix requires authentication to use it's API
    hook_config = {'server': SERVER, 'itemid': ITEMID}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_key_no_auth_data_bails():
    # This test should exit early since there is no authentication provided
    # and Zabbix requires authentication to use it's API
    hook_config = {'server': SERVER, 'host': HOST, 'key': KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_key_with_api_key_auth_data_successful():
    # This test should simulate a successful POST to a Zabbix server. This test uses API_KEY
    # to authenticate and HOST/KEY to know which item to populate in Zabbix.
    hook_config = {'server': SERVER, 'host': HOST, 'key': KEY, 'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
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
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_missing_key_bails():
    hook_config = {'server': SERVER, 'host': HOST, 'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_key_and_missing_host_bails():
    hook_config = {'server': SERVER, 'key': KEY, 'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_key_with_username_password_auth_data_successful():
    # This test should simulate a successful POST to a Zabbix server. This test uses USERNAME/PASSWORD
    # to authenticate and HOST/KEY to know which item to populate in Zabbix.
    hook_config = {
        'server': SERVER,
        'host': HOST,
        'key': KEY,
        'username': USERNAME,
        'password': PASSWORD,
    }

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    auth_response = flexmock(ok=True)
    auth_response.should_receive('json').and_return(
        {'jsonrpc': '2.0', 'result': '3fe6ed01a69ebd79907a120bcd04e494', 'id': 1}
    )

    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_USER_LOGIN,
    ).and_return(auth_response).once()

    flexmock(module.logger).should_receive('warning').never()

    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_HOST_KEY_WITH_KEY_VALUE,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_key_with_username_password_auth_data_and_auth_post_error_bails():
    hook_config = {
        'server': SERVER,
        'host': HOST,
        'key': KEY,
        'username': USERNAME,
        'password': PASSWORD,
    }

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    auth_response = flexmock(ok=False)
    auth_response.should_receive('json').and_return(
        {'jsonrpc': '2.0', 'result': '3fe6ed01a69ebd79907a120bcd04e494', 'id': 1}
    )
    auth_response.should_receive('raise_for_status').and_raise(
        module.requests.ConnectionError
    ).once()

    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_USER_LOGIN,
    ).and_return(auth_response).once()
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_HOST_KEY_WITH_KEY_VALUE,
    ).never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_key_with_username_and_missing_password_bails():
    hook_config = {
        'server': SERVER,
        'host': HOST,
        'key': KEY,
        'username': USERNAME,
    }

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_host_and_key_with_password_and_missing_username_bails():
    hook_config = {
        'server': SERVER,
        'host': HOST,
        'key': KEY,
        'password': PASSWORD,
    }

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_itemid_with_api_key_auth_data_successful():
    # This test should simulate a successful POST to a Zabbix server. This test uses API_KEY
    # to authenticate and HOST/KEY to know which item to populate in Zabbix.
    hook_config = {'server': SERVER, 'itemid': ITEMID, 'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_API_KEY,
        json=DATA_ITEMID,
    ).and_return(flexmock(ok=True)).once()
    flexmock(module.logger).should_receive('warning').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_itemid_with_username_password_auth_data_successful():
    # This test should simulate a successful POST to a Zabbix server. This test uses USERNAME/PASSWORD
    # to authenticate and HOST/KEY to know which item to populate in Zabbix.
    hook_config = {'server': SERVER, 'itemid': ITEMID, 'username': USERNAME, 'password': PASSWORD}

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    auth_response = flexmock(ok=True)
    auth_response.should_receive('json').and_return(
        {'jsonrpc': '2.0', 'result': '3fe6ed01a69ebd79907a120bcd04e494', 'id': 1}
    )

    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_USER_LOGIN,
    ).and_return(auth_response).once()

    flexmock(module.logger).should_receive('warning').never()

    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_HOST_KEY_WITH_ITEMID,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_itemid_with_username_password_auth_data_and_push_post_error_bails():
    hook_config = {'server': SERVER, 'itemid': ITEMID, 'username': USERNAME, 'password': PASSWORD}

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value: value)
    auth_response = flexmock(ok=True)
    auth_response.should_receive('json').and_return(
        {'jsonrpc': '2.0', 'result': '3fe6ed01a69ebd79907a120bcd04e494', 'id': 1}
    )

    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_USER_LOGIN,
    ).and_return(auth_response).once()

    push_response = flexmock(ok=False)
    push_response.should_receive('raise_for_status').and_raise(
        module.requests.ConnectionError
    ).once()
    flexmock(module.requests).should_receive('post').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_USERNAME_PASSWORD,
        json=DATA_HOST_KEY_WITH_ITEMID,
    ).and_return(push_response).once()

    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_credential_error_bails():
    hook_config = {'server': SERVER, 'itemid': ITEMID, 'username': USERNAME, 'password': PASSWORD}

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_raise(ValueError)
    flexmock(module.requests).should_receive('post').never()
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
