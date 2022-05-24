from flexmock import flexmock

from borgmatic.hooks import cronitor as module


def test_ping_monitor_hits_ping_url_for_start_state():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').with_args('https://example.com/run')

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_finish_state():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').with_args('https://example.com/complete')

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_fail_state():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').with_args('https://example.com/fail')

    module.ping_monitor(
        hook_config, 'config.yaml', module.monitor.State.FAIL, monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config, 'config.yaml', module.monitor.State.START, monitoring_log_level=1, dry_run=True
    )


def test_ping_monitor_with_connection_error_does_not_raise():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').and_raise(
        module.requests.exceptions.ConnectionError
    )

    module.ping_monitor(
        hook_config,
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )
