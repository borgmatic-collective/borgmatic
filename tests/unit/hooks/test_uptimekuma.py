from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import uptimekuma as module

default_base_url = 'https://example.uptime.kuma'
custom_base_url = 'https://uptime.example.com'
push_code = 'abcd1234'


def test_ping_monitor_hits_default_uptimekuma_on_fail():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{default_base_url}/api/push/{push_code}?status=down&msg=fail&ping='
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_custom_uptimekuma_on_fail():
    hook_config = {'server': custom_base_url, 'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{custom_base_url}/api/push/{push_code}?status=down&msg=fail&ping='
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_default_uptimekuma_on_start():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{default_base_url}/api/push/{push_code}?status=up&msg=start&ping='
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_custom_uptimekuma_on_start():
    hook_config = {'server': custom_base_url, 'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{custom_base_url}/api/push/{push_code}?status=up&msg=start&ping='
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_default_uptimekuma_on_finish():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{default_base_url}/api/push/{push_code}?status=up&msg=finish&ping='
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_custom_uptimekuma_on_finish():
    hook_config = {'server': custom_base_url, 'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{custom_base_url}/api/push/{push_code}?status=up&msg=finish&ping='
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_does_not_hit_default_uptimekuma_on_fail_dry_run():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_custom_uptimekuma_on_fail_dry_run():
    hook_config = {'server': custom_base_url, 'push_code': push_code}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_default_uptimekuma_on_start_dry_run():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_custom_uptimekuma_on_start_dry_run():
    hook_config = {'server': custom_base_url, 'push_code': push_code}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_default_uptimekuma_on_finish_dry_run():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_custom_uptimekuma_on_finish_dry_run():
    hook_config = {'server': custom_base_url, 'push_code': push_code}
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    hook_config = {'push_code': push_code}
    flexmock(module.requests).should_receive('get').with_args(
        f'{default_base_url}/api/push/{push_code}?status=down&msg=fail&ping='
    ).and_raise(module.requests.exceptions.ConnectionError)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_other_error_logs_warning():
    hook_config = {'push_code': push_code}
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException
    )
    flexmock(module.requests).should_receive('post').with_args(
        f'{default_base_url}/api/push/{push_code}?status=down&msg=fail&ping='
    ).and_return(response)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
