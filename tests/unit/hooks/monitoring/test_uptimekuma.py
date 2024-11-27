from flexmock import flexmock

import borgmatic.hooks.monitoring.monitor
from borgmatic.hooks.monitoring import uptime_kuma as module

DEFAULT_PUSH_URL = 'https://example.uptime.kuma/api/push/abcd1234'
CUSTOM_PUSH_URL = 'https://uptime.example.com/api/push/efgh5678'


def test_ping_monitor_hits_default_uptimekuma_on_fail():
    hook_config = {}
    flexmock(module.requests).should_receive('get').with_args(
        f'{DEFAULT_PUSH_URL}?status=down&msg=fail'
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_custom_uptimekuma_on_fail():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').with_args(
        f'{CUSTOM_PUSH_URL}?status=down&msg=fail'
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_custom_uptimekuma_on_start():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').with_args(
        f'{CUSTOM_PUSH_URL}?status=up&msg=start'
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_custom_uptimekuma_on_finish():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').with_args(
        f'{CUSTOM_PUSH_URL}?status=up&msg=finish'
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_does_not_hit_custom_uptimekuma_on_fail_dry_run():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_custom_uptimekuma_on_start_dry_run():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_custom_uptimekuma_on_finish_dry_run():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').with_args(
        f'{CUSTOM_PUSH_URL}?status=down&msg=fail'
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


def test_ping_monitor_with_other_error_logs_warning():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException
    )
    flexmock(module.requests).should_receive('get').with_args(
        f'{CUSTOM_PUSH_URL}?status=down&msg=fail'
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


def test_ping_monitor_with_invalid_run_state():
    hook_config = {'push_url': CUSTOM_PUSH_URL}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=True,
    )
