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
}

DATA_USER_LOGIN = {
    'jsonrpc': '2.0',
    'method': 'user.login',
    'params': {'username': USERNAME, 'password': PASSWORD},
    'id': 1,
}

DATA_USER_LOGOUT = {
    'jsonrpc': '2.0',
    'method': 'user.logout',
    'params': [],
    'id': 1,
}

AUTH_HEADERS_LOGIN = {
    'Content-Type': 'application/json-rpc',
    'User-Agent': 'borgmatic',
}

AUTH_HEADERS = {
    'Content-Type': 'application/json-rpc',
    'Authorization': f'Bearer {API_KEY}',
    'User-Agent': 'borgmatic',
}


def test_send_zabbix_request_with_post_error_bails():
    server = flexmock()
    headers = flexmock()
    data = {'method': 'do.stuff'}
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException,
    )

    flexmock(module.requests).should_receive('post').with_args(
        server,
        headers=headers,
        json=data,
        timeout=int,
    ).and_return(response)

    assert module.send_zabbix_request(server, headers, data) is None


def test_send_zabbix_request_with_invalid_json_response_bails():
    server = flexmock()
    headers = flexmock()
    data = {'method': 'do.stuff'}
    flexmock(module.requests.exceptions.JSONDecodeError).should_receive('__init__')
    response = flexmock(ok=True)
    response.should_receive('json').and_raise(module.requests.exceptions.JSONDecodeError)

    flexmock(module.requests).should_receive('post').with_args(
        server,
        headers=headers,
        json=data,
        timeout=int,
    ).and_return(response)

    assert module.send_zabbix_request(server, headers, data) is None


def test_send_zabbix_request_with_success_returns_response_result():
    server = flexmock()
    headers = flexmock()
    data = {'method': 'do.stuff'}
    response = flexmock(ok=True)
    response.should_receive('json').and_return({'result': {'foo': 'bar'}})

    flexmock(module.requests).should_receive('post').with_args(
        server,
        headers=headers,
        json=data,
        timeout=int,
    ).and_return(response)

    assert module.send_zabbix_request(server, headers, data) == {'foo': 'bar'}


def test_send_zabbix_request_with_success_passes_through_missing_result():
    server = flexmock()
    headers = flexmock()
    data = {'method': 'do.stuff'}
    response = flexmock(ok=True)
    response.should_receive('json').and_return({})

    flexmock(module.requests).should_receive('post').with_args(
        server,
        headers=headers,
        json=data,
        timeout=int,
    ).and_return(response)

    assert module.send_zabbix_request(server, headers, data) is None


def test_send_zabbix_request_with_error_bails():
    server = flexmock()
    headers = flexmock()
    data = {'method': 'do.stuff'}
    response = flexmock(ok=True)
    response.should_receive('json').and_return({'result': {'data': [{'error': 'oops'}]}})

    flexmock(module.requests).should_receive('post').with_args(
        server,
        headers=headers,
        json=data,
        timeout=int,
    ).and_return(response)

    assert module.send_zabbix_request(server, headers, data) is None


def test_ping_monitor_with_non_matching_state_bails():
    hook_config = {'api_key': API_KEY}
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_HOST_KEY,
    ).once()
    flexmock(module.logger).should_receive('warning').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_adds_missing_api_endpoint_to_server_url():
    # This test should simulate a successful POST to a Zabbix server. This test uses API_KEY
    # to authenticate and HOST/KEY to know which item to populate in Zabbix.
    hook_config = {'server': SERVER, 'host': HOST, 'key': KEY, 'api_key': API_KEY}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_HOST_KEY,
    ).once()
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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_LOGIN,
        data=DATA_USER_LOGIN,
    ).and_return('fakekey').once()

    flexmock(module.logger).should_receive('warning').never()

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_HOST_KEY_WITH_KEY_VALUE,
    ).once()

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_USER_LOGOUT,
    ).once()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_LOGIN,
        data=DATA_USER_LOGIN,
    ).and_return(None).once()
    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_HOST_KEY_WITH_KEY_VALUE,
    ).never()

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_USER_LOGOUT,
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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('send_zabbix_request').never()

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
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_ITEMID,
    ).once()
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
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS_LOGIN,
        data=DATA_USER_LOGIN,
    ).and_return('fakekey').once()

    flexmock(module.logger).should_receive('warning').never()

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_HOST_KEY_WITH_ITEMID,
    ).once()

    flexmock(module).should_receive('send_zabbix_request').with_args(
        f'{SERVER}',
        headers=AUTH_HEADERS,
        data=DATA_USER_LOGOUT,
    ).once()

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
        'resolve_credential',
    ).and_raise(ValueError)
    flexmock(module).should_receive('send_zabbix_request').never()
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
