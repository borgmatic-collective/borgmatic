from flexmock import flexmock

from borgmatic.hooks import healthchecks as module


def test_forgetful_buffering_handler_emit_collects_log_records():
    handler = module.Forgetful_buffering_handler(byte_capacity=100)
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    handler.emit(flexmock(getMessage=lambda: 'bar'))

    assert handler.buffer == ['foo\n', 'bar\n']
    assert not handler.forgot


def test_forgetful_buffering_handler_emit_forgets_log_records_when_capacity_reached():
    handler = module.Forgetful_buffering_handler(byte_capacity=len('foo\nbar\n'))
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    assert handler.buffer == ['foo\n']
    handler.emit(flexmock(getMessage=lambda: 'bar'))
    assert handler.buffer == ['foo\n', 'bar\n']
    handler.emit(flexmock(getMessage=lambda: 'baz'))
    assert handler.buffer == ['bar\n', 'baz\n']
    handler.emit(flexmock(getMessage=lambda: 'quux'))
    assert handler.buffer == ['quux\n']
    assert handler.forgot


def test_format_buffered_logs_for_payload_flattens_log_buffer():
    handler = module.Forgetful_buffering_handler(byte_capacity=100)
    handler.buffer = ['foo\n', 'bar\n']
    flexmock(module.logging).should_receive('getLogger').and_return(flexmock(handlers=[handler]))

    payload = module.format_buffered_logs_for_payload()

    assert payload == 'foo\nbar\n'


def test_format_buffered_logs_for_payload_inserts_truncation_indicator_when_logs_forgotten():
    handler = module.Forgetful_buffering_handler(byte_capacity=100)
    handler.buffer = ['foo\n', 'bar\n']
    handler.forgot = True
    flexmock(module.logging).should_receive('getLogger').and_return(flexmock(handlers=[handler]))

    payload = module.format_buffered_logs_for_payload()

    assert payload == '...\nfoo\nbar\n'


def test_format_buffered_logs_for_payload_without_handler_produces_empty_payload():
    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(handlers=[module.logging.Handler()])
    )

    payload = module.format_buffered_logs_for_payload()

    assert payload == ''


def test_ping_monitor_hits_ping_url_for_start_state():
    flexmock(module).should_receive('Forgetful_buffering_handler')
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('post').with_args(
        '{}/{}'.format(ping_url, 'start'), data=''
    )

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.START, dry_run=False)


def test_ping_monitor_hits_ping_url_for_finish_state():
    ping_url = 'https://example.com'
    payload = flexmock()
    flexmock(module).should_receive('format_buffered_logs_for_payload').and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(ping_url, data=payload)

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.FINISH, dry_run=False)


def test_ping_monitor_hits_ping_url_for_fail_state():
    ping_url = 'https://example.com'
    payload = flexmock()
    flexmock(module).should_receive('format_buffered_logs_for_payload').and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        '{}/{}'.format(ping_url, 'fail'), data=payload
    )

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.FAIL, dry_run=False)


def test_ping_monitor_with_ping_uuid_hits_corresponding_url():
    ping_uuid = 'abcd-efgh-ijkl-mnop'
    payload = flexmock()
    flexmock(module).should_receive('format_buffered_logs_for_payload').and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://hc-ping.com/{}'.format(ping_uuid), data=payload
    )

    module.ping_monitor(ping_uuid, 'config.yaml', state=module.monitor.State.FINISH, dry_run=False)


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    flexmock(module).should_receive('Forgetful_buffering_handler')
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(ping_url, 'config.yaml', state=module.monitor.State.START, dry_run=True)
