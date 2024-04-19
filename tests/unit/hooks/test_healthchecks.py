from flexmock import flexmock

from borgmatic.hooks import healthchecks as module


def mock_logger():
    logger = flexmock()
    logger.should_receive('addHandler')
    logger.should_receive('removeHandler')
    flexmock(module.logging).should_receive('getLogger').and_return(logger)


def test_initialize_monitor_creates_log_handler_with_ping_body_limit():
    ping_body_limit = 100
    monitoring_log_level = 1

    mock_logger()
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').with_args(
        module.HANDLER_IDENTIFIER,
        ping_body_limit - len(module.borgmatic.hooks.logs.PAYLOAD_TRUNCATION_INDICATOR),
        monitoring_log_level,
    ).once()

    module.initialize_monitor(
        {'ping_body_limit': ping_body_limit}, {}, 'test.yaml', monitoring_log_level, dry_run=False
    )


def test_initialize_monitor_creates_log_handler_with_default_ping_body_limit():
    monitoring_log_level = 1

    mock_logger()
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').with_args(
        module.HANDLER_IDENTIFIER,
        module.DEFAULT_PING_BODY_LIMIT_BYTES
        - len(module.borgmatic.hooks.logs.PAYLOAD_TRUNCATION_INDICATOR),
        monitoring_log_level,
    ).once()

    module.initialize_monitor({}, {}, 'test.yaml', monitoring_log_level, dry_run=False)


def test_initialize_monitor_creates_log_handler_with_zero_ping_body_limit():
    ping_body_limit = 0
    monitoring_log_level = 1

    mock_logger()
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').with_args(
        module.HANDLER_IDENTIFIER, ping_body_limit, monitoring_log_level
    ).once()

    module.initialize_monitor(
        {'ping_body_limit': ping_body_limit}, {}, 'test.yaml', monitoring_log_level, dry_run=False
    )


def test_initialize_monitor_creates_log_handler_when_send_logs_true():
    mock_logger()
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').once()

    module.initialize_monitor(
        {'send_logs': True}, {}, 'test.yaml', monitoring_log_level=1, dry_run=False
    )


def test_initialize_monitor_bails_when_send_logs_false():
    mock_logger()
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()

    module.initialize_monitor(
        {'send_logs': False}, {}, 'test.yaml', monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_hits_ping_url_for_start_state():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_finish_state():
    hook_config = {'ping_url': 'https://example.com'}
    payload = 'data'
    flexmock(module.borgmatic.hooks.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com', data=payload.encode('utf-8'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_fail_state():
    hook_config = {'ping_url': 'https://example.com'}
    payload = 'data'
    flexmock(module.borgmatic.hooks.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/fail', data=payload.encode('utf'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_ping_url_for_log_state():
    hook_config = {'ping_url': 'https://example.com'}
    payload = 'data'
    flexmock(module.borgmatic.hooks.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/log', data=payload.encode('utf'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_ping_uuid_hits_corresponding_url():
    hook_config = {'ping_url': 'abcd-efgh-ijkl-mnop'}
    payload = 'data'
    flexmock(module.borgmatic.hooks.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        f"https://hc-ping.com/{hook_config['ping_url']}",
        data=payload.encode('utf-8'),
        verify=True,
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_skips_ssl_verification_when_verify_tls_false():
    hook_config = {'ping_url': 'https://example.com', 'verify_tls': False}
    payload = 'data'
    flexmock(module.borgmatic.hooks.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com', data=payload.encode('utf-8'), verify=False
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_executes_ssl_verification_when_verify_tls_true():
    hook_config = {'ping_url': 'https://example.com', 'verify_tls': True}
    payload = 'data'
    flexmock(module.borgmatic.hooks.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return(payload)
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com', data=payload.encode('utf-8'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_dry_run_does_not_hit_ping_url():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_ping_url_when_states_not_matching():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com', 'states': ['finish']}
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_hits_ping_url_when_states_matching():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com', 'states': ['start', 'finish']}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_adds_create_query_parameter_when_create_slug_true():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com', 'create_slug': True}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start?create=1', data=''.encode('utf-8'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_does_not_add_create_query_parameter_when_create_slug_false():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com', 'create_slug': False}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8'), verify=True
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_does_not_add_create_query_parameter_when_ping_url_is_uuid():
    hook_config = {'ping_url': 'abcd-efgh-ijkl-mnop', 'create_slug': True}
    flexmock(module.requests).should_receive('post').with_args(
        f"https://hc-ping.com/{hook_config['ping_url']}",
        data=''.encode('utf-8'),
        verify=True,
    ).and_return(flexmock(ok=True))

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com'}
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8'), verify=True
    ).and_raise(module.requests.exceptions.ConnectionError)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_other_error_logs_warning():
    flexmock(module.borgmatic.hooks.logs).should_receive('Forgetful_buffering_handler').never()
    hook_config = {'ping_url': 'https://example.com'}
    response = flexmock(ok=False)
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException
    )
    flexmock(module.requests).should_receive('post').with_args(
        'https://example.com/start', data=''.encode('utf-8'), verify=True
    ).and_return(response)
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        state=module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )
