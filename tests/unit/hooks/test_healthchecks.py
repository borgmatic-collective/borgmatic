from flexmock import flexmock

from borgmatic.hooks import healthchecks as module


def test_ping_monitor_hits_ping_url_for_start_state():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, 'start'))

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.START, dry_run=False)


def test_ping_monitor_hits_ping_url_for_finish_state():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args(ping_url)

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.FINISH, dry_run=False)


def test_ping_monitor_hits_ping_url_for_fail_state():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, 'fail'))

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.FAIL, dry_run=False)


def test_ping_monitor_with_ping_uuid_hits_corresponding_url():
    ping_uuid = 'abcd-efgh-ijkl-mnop'
    flexmock(module.requests).should_receive('get').with_args(
        'https://hc-ping.com/{}'.format(ping_uuid)
    )

    module.ping_monitor(ping_uuid, 'config.yaml', state=module.monitor.State.FINISH, dry_run=False)


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').never()

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.START, dry_run=True)
