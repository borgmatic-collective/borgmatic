from flexmock import flexmock

from borgmatic.hooks import cronhub as module


def test_ping_cronhub_hits_ping_url_with_start_state():
    ping_url = 'https://example.com/start/abcdef'
    state = 'bork'
    flexmock(module.requests).should_receive('get').with_args('https://example.com/bork/abcdef')

    module.ping_cronhub(ping_url, 'config.yaml', dry_run=False, state=state)


def test_ping_cronhub_hits_ping_url_with_ping_state():
    ping_url = 'https://example.com/ping/abcdef'
    state = 'bork'
    flexmock(module.requests).should_receive('get').with_args('https://example.com/bork/abcdef')

    module.ping_cronhub(ping_url, 'config.yaml', dry_run=False, state=state)


def test_ping_cronhub_without_ping_url_does_not_raise():
    flexmock(module.requests).should_receive('get').never()

    module.ping_cronhub(ping_url=None, config_filename='config.yaml', dry_run=False, state='oops')


def test_ping_cronhub_dry_run_does_not_hit_ping_url():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').never()

    module.ping_cronhub(ping_url, 'config.yaml', dry_run=True, state='yay')
