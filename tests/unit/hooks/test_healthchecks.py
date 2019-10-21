from flexmock import flexmock

from borgmatic.hooks import healthchecks as module


def test_ping_healthchecks_hits_ping_url():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args(ping_url)

    module.ping_healthchecks(ping_url, 'config.yaml', dry_run=False)


def test_ping_healthchecks_without_ping_url_does_not_raise():
    flexmock(module.requests).should_receive('get').never()

    module.ping_healthchecks(ping_url_or_uuid=None, config_filename='config.yaml', dry_run=False)


def test_ping_healthchecks_with_ping_uuid_hits_corresponding_url():
    ping_uuid = 'abcd-efgh-ijkl-mnop'
    flexmock(module.requests).should_receive('get').with_args(
        'https://hc-ping.com/{}'.format(ping_uuid)
    )

    module.ping_healthchecks(ping_uuid, 'config.yaml', dry_run=False)


def test_ping_healthchecks_hits_ping_url_with_append():
    ping_url = 'https://example.com'
    append = 'failed-so-hard'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, append))

    module.ping_healthchecks(ping_url, 'config.yaml', dry_run=False, append=append)
