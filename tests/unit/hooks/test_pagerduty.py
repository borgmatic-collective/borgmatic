from flexmock import flexmock

from borgmatic.hooks import pagerduty as module


def test_ping_monitor_ignores_start_state():
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        'abc123', 'config.yaml', module.monitor.State.START, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_ignores_finish_state():
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        'abc123', 'config.yaml', module.monitor.State.FINISH, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_calls_api_for_fail_state():
    flexmock(module.requests).should_receive('post')

    module.ping_monitor(
        'abc123', 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_dry_run_does_not_call_api():
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        'abc123', 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=True
    )
