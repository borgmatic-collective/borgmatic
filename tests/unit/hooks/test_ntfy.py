from enum import Enum

from flexmock import flexmock

from borgmatic.hooks import ntfy as module

default_base_url = 'https://ntfy.sh'
custom_base_url = 'https://ntfy.example.com'
topic = 'borgmatic-unit-testing'

custom_message_config = {
    'title': 'Borgmatic unit testing',
    'message': 'Borgmatic unit testing',
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
    headers = {
        'X-Title': f'A Borgmatic {state.name} event happened',
        'X-Message': f'A Borgmatic {state.name} event happened',
        'X-Priority': 'default',
        'X-Tags': 'borgmatic',
    }
    return headers


def test_ping_monitor_minimal_config_hits_hosted_ntfy_on_fail():
    hook_config = {'topic': topic}
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(module.monitor.State.FAIL),
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config, 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_minimal_config_does_not_hit_hosted_ntfy_on_start():
    hook_config = {'topic': topic}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_minimal_config_does_not_hit_hosted_ntfy_on_finish():
    hook_config = {'topic': topic}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_minimal_config_hits_selfhosted_ntfy_on_fail():
    hook_config = {'topic': topic, 'server': custom_base_url}
    flexmock(module.requests).should_receive('post').with_args(
        f'{custom_base_url}/{topic}',
        headers=return_default_message_headers(module.monitor.State.FAIL),
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config, 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_minimal_config_does_not_hit_hosted_ntfy_on_fail_dry_run():
    hook_config = {'topic': topic}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config, 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=True
    )


def test_ping_monitor_custom_message_hits_hosted_ntfy_on_fail():
    hook_config = {'topic': topic, 'fail': custom_message_config}
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}', headers=custom_message_headers,
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config, 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_custom_state_hits_hosted_ntfy_on_start():
    hook_config = {'topic': topic, 'states': ['start', 'fail']}
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(module.monitor.State.START),
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    hook_config = {'topic': topic}
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(module.monitor.State.FAIL),
    ).and_raise(module.requests.exceptions.ConnectionError)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_other_error_logs_warning():
    hook_config = {'topic': topic}
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException
    )
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/{topic}',
        headers=return_default_message_headers(module.monitor.State.FAIL),
    ).and_return(response)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
