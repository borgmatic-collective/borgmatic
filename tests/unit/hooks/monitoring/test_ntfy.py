from enum import Enum

from flexmock import flexmock

import borgmatic.hooks.monitoring.monitor
from borgmatic.hooks.monitoring import ntfy as module

DEFAULT_BASE_URL = 'https://ntfy.sh'
CUSTOM_BASE_URL = 'https://ntfy.example.com'
TOPIC = 'borgmatic-unit-testing'

CUSTOM_MESSAGE_CONFIG = {
    'title': 'borgmatic unit testing',
    'message': 'borgmatic unit testing',
    'priority': 'min',
    'tags': '+1',
}

CUSTOM_MESSAGE_HEADERS = {
    'User-Agent': 'borgmatic',
}

CUSTOM_MESSAGE_PAYLOAD = {
    'topic': TOPIC,
    'title': CUSTOM_MESSAGE_CONFIG['title'],
    'message': CUSTOM_MESSAGE_CONFIG['message'],
    'priority': 1,
    'tags': [CUSTOM_MESSAGE_CONFIG['tags']],
}


def default_message_payload(state=Enum):
    return {
        'topic': TOPIC,
        'title': f'A borgmatic {state.name} event happened',
        'message': f'A borgmatic {state.name} event happened',
        'priority': 3,
        'tags': ['borgmatic'],
    }


def test_ping_monitor_minimal_config_hits_hosted_ntfy_on_fail():
    hook_config = {'topic': TOPIC}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
        'topic': TOPIC,
        'access_token': 'abc123',
    }
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=dict(CUSTOM_MESSAGE_HEADERS, Authorization='Bearer abc123'),
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
        'topic': TOPIC,
        'username': 'testuser',
        'password': 'fakepassword',
        'access_token': 'abc123',
    }
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=dict(CUSTOM_MESSAGE_HEADERS, Authorization='Bearer abc123'),
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
        'topic': TOPIC,
        'username': 'testuser',
        'password': 'fakepassword',
    }
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=module.requests.auth.HTTPBasicAuth('testuser', 'fakepassword'),
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
    hook_config = {'topic': TOPIC, 'password': 'fakepassword'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
    hook_config = {'topic': TOPIC, 'username': 'testuser'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
    hook_config = {'topic': TOPIC}
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
    hook_config = {'topic': TOPIC}
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
    hook_config = {'topic': TOPIC, 'server': CUSTOM_BASE_URL}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        CUSTOM_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
    hook_config = {'topic': TOPIC}
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
    hook_config = {'topic': TOPIC, 'fail': CUSTOM_MESSAGE_CONFIG}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=CUSTOM_MESSAGE_PAYLOAD,
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
    hook_config = {'topic': TOPIC, 'states': ['start', 'fail']}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.START),
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
    hook_config = {'topic': TOPIC}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
    hook_config = {'topic': TOPIC}
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
    hook_config = {'topic': TOPIC}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException,
    )
    flexmock(module.requests).should_receive('post').with_args(
        DEFAULT_BASE_URL,
        auth=None,
        timeout=int,
        headers=CUSTOM_MESSAGE_HEADERS,
        json=default_message_payload(borgmatic.hooks.monitoring.monitor.State.FAIL),
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
