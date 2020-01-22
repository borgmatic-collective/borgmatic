from flexmock import flexmock

from borgmatic.hooks import cronitor as module


def test_ping_monitor_hits_ping_url_for_start_state():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, 'run'))

    module.ping_monitor(
        ping_url, 'config.yaml', module.monitor.State.START, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_hits_ping_url_for_finish_state():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, 'complete'))

    module.ping_monitor(
        ping_url, 'config.yaml', module.monitor.State.FINISH, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_hits_ping_url_for_fail_state():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, 'fail'))

    module.ping_monitor(
        ping_url, 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        ping_url, 'config.yaml', module.monitor.State.START, monitoring_log_level=1, dry_run=True
    )
