from flexmock import flexmock

from borgmatic.hooks import healthchecks as module


def test_forgetful_buffering_handler_emit_collects_log_records():
    handler = module.Forgetful_buffering_handler(byte_capacity=100, log_level=1)
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    handler.emit(flexmock(getMessage=lambda: 'bar'))

    assert handler.buffer == ['foo\n', 'bar\n']
    assert not handler.forgot


def test_forgetful_buffering_handler_emit_collects_log_records_with_zero_byte_capacity():
    handler = module.Forgetful_buffering_handler(byte_capacity=0, log_level=1)
    handler.emit(flexmock(getMessage=lambda: 'foo'))
    handler.emit(flexmock(getMessage=lambda: 'bar'))

    assert handler.buffer == ['foo\n', 'bar\n']
    assert not handler.forgot


def test_forgetful_buffering_handler_emit_forgets_log_records_when_capacity_reached():
    handler = module.Forgetful_buffering_handler(byte_capacity=len('foo\nbar\n'), log_level=1)
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
    handler = module.Forgetful_buffering_handler(byte_capacity=100, log_level=1)
    handler.buffer = ['foo\n', 'bar\n']
    logger = flexmock(handlers=[handler])
    logger.should_receive('removeHandler')
    flexmock(module.logging).should_receive('getLogger').and_return(logger)

    payload = module.format_buffered_logs_for_payload()

    assert payload == 'foo\nbar\n'


def test_format_buffered_logs_for_payload_inserts_truncation_indicator_when_logs_forgotten():
    handler = module.Forgetful_buffering_handler(byte_capacity=100, log_level=1)
    handler.buffer = ['foo\n', 'bar\n']
    handler.forgot = True
    logger = flexmock(handlers=[handler])
    logger.should_receive('removeHandler')
    flexmock(module.logging).should_receive('getLogger').and_return(logger)

    payload = module.format_buffered_logs_for_payload()

    assert payload == '...\nfoo\nbar\n'


def test_format_buffered_logs_for_payload_without_handler_produces_empty_payload():
    logger = flexmock(handlers=[module.logging.Handler()])
    logger.should_receive('removeHandler')
    flexmock(module.logging).should_receive('getLogger').and_return(logger)

    payload = module.format_buffered_logs_for_payload()

    assert payload == ''


def test_initialize_monitor_creates_log_handler_with_ping_body_limit():
    ping_body_limit = 100
    monitoring_log_level = 1

    flexmock(module).should_receive('Forgetful_buffering_handler').with_args(
        ping_body_limit - len(module.PAYLOAD_TRUNCATION_INDICATOR), monitoring_log_level
    ).once()

    module.initialize_monitor(
        {'ping_body_limit': ping_body_limit}, 'test.yaml', monitoring_log_level, dry_run=False
    )


def test_initialize_monitor_creates_log_handler_with_default_ping_body_limit():
    monitoring_log_level = 1

    flexmock(module).should_receive('Forgetful_buffering_handler').with_args(
        module.DEFAULT_PING_BODY_LIMIT_BYTES - len(module.PAYLOAD_TRUNCATION_INDICATOR),
        monitoring_log_level,
    ).once()

    module.initialize_monitor({}, 'test.yaml', monitoring_log_level, dry_run=False)


def test_initialize_monitor_creates_log_handler_with_zero_ping_body_limit():
    ping_body_limit = 0
    monitoring_log_level = 1

    flexmock(module).should_receive('Forgetful_buffering_handler').with_args(
        ping_body_limit, monitoring_log_level
    ).once()

    module.initialize_monitor(
        {'ping_body_limit': ping_body_limit}, 'test.yaml', monitoring_log_level, dry_run=False
    )


def test_ping_monitor_hits_ping_url_for_start_state():
    flexmock(module).should_receive('Forgetful_buffering_handler')
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8')
    )

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_finish_state():
    hook_config = {'ping_url': 'https://example.com'}
    payload = 'data'
    flexmock(module).should_receive('format_buffered_logs_for_payload').and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com', data=payload.encode('utf-8')
    )

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_fail_state():
    hook_config = {'ping_url': 'https://example.com'}
    payload = 'data'
    flexmock(module).should_receive('format_buffered_logs_for_payload').and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/fail', data=payload.encode('utf')
    )

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_ping_uuid_hits_corresponding_url():
    hook_config = {'ping_url': 'abcd-efgh-ijkl-mnop'}
    payload = 'data'
    flexmock(module).should_receive('format_buffered_logs_for_payload').and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://hc-ping.com/{}'.format(hook_config['ping_url']), data=payload.encode('utf-8')
    )

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    flexmock(module).should_receive('Forgetful_buffering_handler')
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_skip_states_does_not_hit_ping_url():
    flexmock(module).should_receive('Forgetful_buffering_handler')
    hook_config = {'ping_url': 'https://example.com', 'skip_states': ['start']}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_hits_ping_url_with_non_matching_skip_states():
    flexmock(module).should_receive('Forgetful_buffering_handler')
    hook_config = {'ping_url': 'https://example.com', 'skip_states': ['finish']}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8')
    )

    module.ping_monitor(
        hook_config,
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )
