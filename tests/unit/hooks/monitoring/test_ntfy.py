from enum import Enum

from flexmock import flexmock

import borgmatic.hooks.monitoring.monitor
from borgmatic.hooks.monitoring import ntfy as module

default_base_url = 'https://ntfy.sh'
custom_base_url = 'https://ntfy.example.com'
topic = 'borgmatic-unit-testing'

custom_message_config = {
    'title': 'borgmatic unit testing',
    'message': 'borgmatic unit testing',
    'priority': 'min',
    'tags': '+1',
}

custom_message_headers = {
    'X-Title': custom_message_config['title'],
    'X-Message': custom_message_config['message'],
    'X-Priority': custom_message_config['priority'],
    'X-Tags': custom_message_config['tags'],
}


def return_default_message_headers(state=Enum):
    return {
        'X-Title': f'A borgmatic {state.name} event happened',
        'X-Message': f'A borgmatic {state.name} event happened',
        'X-Priority': 'default',
        'X-Tags': 'borgmatic',
    }


def test_ping_monitor_minimal_config_hits_hosted_ntfy_on_fail():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=None,
        timeout=int,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_access_token_hits_hosted_ntfy_on_fail():
    hook_config = {
        'topic': topic,
        'access_token': 'abc123',
    }
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=module.requests.auth.HTTPBasicAuth('', 'abc123'),
        timeout=int,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_username_password_and_access_token_ignores_username_password():
    hook_config = {
        'topic': topic,
        'username': 'testuser',
        'password': 'fakepassword',
        'access_token': 'abc123',
    }
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=module.requests.auth.HTTPBasicAuth('', 'abc123'),
        timeout=int,
    ).and_return(flexmock(ok=True)).once()
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_username_password_hits_hosted_ntfy_on_fail():
    hook_config = {
        'topic': topic,
        'username': 'testuser',
        'password': 'fakepassword',
    }
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=module.requests.auth.HTTPBasicAuth('testuser', 'fakepassword'),
        timeout=int,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_password_but_no_username_warns():
    hook_config = {'topic': topic, 'password': 'fakepassword'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=None,
        timeout=int,
    ).and_return(flexmock(ok=True)).once()
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_username_but_no_password_warns():
    hook_config = {'topic': topic, 'username': 'testuser'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=None,
        timeout=int,
    ).and_return(flexmock(ok=True)).once()
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_minimal_config_does_not_hit_hosted_ntfy_on_start():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_minimal_config_does_not_hit_hosted_ntfy_on_finish():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_minimal_config_hits_selfhosted_ntfy_on_fail():
    hook_config = {'topic': topic, 'server': custom_base_url}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{custom_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=None,
        timeout=int,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_minimal_config_does_not_hit_hosted_ntfy_on_fail_dry_run():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_custom_message_hits_hosted_ntfy_on_fail():
    hook_config = {'topic': topic, 'fail': custom_message_config}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=custom_message_headers,
        auth=None,
        timeout=int,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_custom_state_hits_hosted_ntfy_on_start():
    hook_config = {'topic': topic, 'states': ['start', 'fail']}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.START),
        auth=None,
        timeout=int,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=None,
        timeout=int,
    ).and_raise(module.requests.exceptions.ConnectionError)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_credential_error_logs_warning():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
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


def test_ping_monitor_with_other_error_logs_warning():
    hook_config = {'topic': topic}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException,
    )
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(borgmatic.hooks.monitoring.monitor.State.FAIL),
        auth=None,
        timeout=int,
    ).and_return(response)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
