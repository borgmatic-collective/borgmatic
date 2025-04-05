from flexmock import flexmock

from borgmatic.hooks.monitoring import pagerduty as module


def test_initialize_monitor_creates_log_handler():
    monitoring_log_level = 1

    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'Forgetful_buffering_handler'
    ).once()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('add_handler')

    module.initialize_monitor({}, {}, 'test.yaml', monitoring_log_level, dry_run=False)


def test_initialize_monitor_creates_log_handler_when_send_logs_true():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'Forgetful_buffering_handler'
    ).once()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('add_handler')

    module.initialize_monitor(
        {'send_logs': True}, {}, 'test.yaml', monitoring_log_level=1, dry_run=False
    )


def test_initialize_monitor_bails_when_send_logs_false():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'Forgetful_buffering_handler'
    ).never()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('add_handler')

    module.initialize_monitor(
        {'send_logs': False}, {}, 'test.yaml', monitoring_log_level=1, dry_run=False
    )


def test_ping_monitor_ignores_start_state():
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_ignores_finish_state():
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_calls_api_for_fail_state():
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy\nlogs')
    flexmock(module.requests).should_receive('post').and_return(flexmock(ok=True))

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_dry_run_does_not_call_api():
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy\nlogs')
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_connection_error_logs_warning():
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy\nlogs')
    flexmock(module.requests).should_receive('post').and_raise(
        module.requests.exceptions.ConnectionError
    )
    flexmock(module.logger).should_receive('warning').once()

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_credential_error_logs_warning():
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_raise(ValueError)
    flexmock(module.requests).should_receive('post').never()
    flexmock(module.logger).should_receive('warning')

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_other_error_logs_warning():
    response = flexmock(ok=False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy\nlogs')
    response.should_receive('raise_for_status').and_raise(
        module.requests.exceptions.RequestException
    )
    flexmock(module.requests).should_receive('post').and_return(response)
    flexmock(module.logger).should_receive('warning')

    module.ping_monitor(
        {'integration_key': 'abc123'},
        {},
        'config.yaml',
        module.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
