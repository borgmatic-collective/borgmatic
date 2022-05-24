from flexmock import flexmock

from borgmatic.hooks import pagerduty as module


def test_ping_monitor_ignores_start_state():
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_ignores_finish_state():
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        'config.yaml',
        module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_calls_api_for_fail_state():
    flexmock(module.requests).should_receive('post')

    module.ping_monitor(
        {'integration_key': 'abc123'},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_dry_run_does_not_call_api():
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_connection_error_does_not_raise():
    flexmock(module.requests).should_receive('post').and_raise(
        module.requests.exceptions.ConnectionError
    )
    flexmock(module.logger).should_receive('warning')

    module.ping_monitor(
        {'integration_key': 'abc123'},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
