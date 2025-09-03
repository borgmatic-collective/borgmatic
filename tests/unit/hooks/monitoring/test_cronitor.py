from flexmock import flexmock

from borgmatic.hooks.monitoring import cronitor as module


def test_ping_monitor_hits_ping_url_for_start_state():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').with_args(
        'https://example.com/run',
        timeout=int,
        headers={'User-Agent': 'borgmatic'},
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_finish_state():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').with_args(
        'https://example.com/complete',
        timeout=int,
        headers={'User-Agent': 'borgmatic'},
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_fail_state():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').with_args(
        'https://example.com/fail',
        timeout=int,
        headers={'User-Agent': 'borgmatic'},
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').and_raise(
        module.requests.exceptions.ConnectionError,
    )
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_other_error_logs_warning():
    hook_config = {'ping_url': 'https://example.com'}
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException,
    )
    flexmock(module.requests).should_receive('get').with_args(
        'https://example.com/run',
        timeout=int,
        headers={'User-Agent': 'borgmatic'},
    ).and_return(response)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_unsupported_monitoring_state_bails():
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        module.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=False,
    )
