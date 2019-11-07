from flexmock import flexmock

from borgmatic.hooks import cronitor as module


def test_ping_cronitor_hits_ping_url():
    ping_url = 'https://example.com'
    append = 'failed-so-hard'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, append))

    module.ping_cronitor(ping_url, 'config.yaml', dry_run=False, append=append)


def test_ping_cronitor_without_ping_url_does_not_raise():
    flexmock(module.requests).should_receive('get').never()

    module.ping_cronitor(ping_url=None, config_filename='config.yaml', dry_run=False, append='oops')


def test_ping_cronitor_dry_run_does_not_hit_ping_url():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').never()

    module.ping_cronitor(ping_url, 'config.yaml', dry_run=True, append='yay')
