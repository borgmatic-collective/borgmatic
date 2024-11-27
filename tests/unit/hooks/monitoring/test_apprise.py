import apprise
from apprise import NotifyFormat, NotifyType
from flexmock import flexmock

import borgmatic.hooks.monitoring.monitor
from borgmatic.hooks.monitoring import apprise as module

TOPIC = 'borgmatic-unit-testing'


def mock_apprise():
    apprise_mock = flexmock(
        add=lambda servers: None, notify=lambda title, body, body_format, notify_type: None
    )
    flexmock(apprise.Apprise).new_instances(apprise_mock)

    return apprise_mock


def test_initialize_monitor_with_send_logs_false_does_not_add_handler():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('add_handler').never()

    module.initialize_monitor(
        hook_config={'send_logs': False},
        config={},
        config_filename='test.yaml',
        monitoring_log_level=1,
        dry_run=False,
    )


def test_initialize_monitor_with_send_logs_true_adds_handler_with_default_log_size_limit():
    truncation_indicator_length = 4
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'Forgetful_buffering_handler'
    ).with_args(
        module.HANDLER_IDENTIFIER,
        module.DEFAULT_LOGS_SIZE_LIMIT_BYTES - truncation_indicator_length,
        1,
    ).once()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('add_handler').once()

    module.initialize_monitor(
        hook_config={'send_logs': True},
        config={},
        config_filename='test.yaml',
        monitoring_log_level=1,
        dry_run=False,
    )


def test_initialize_monitor_without_send_logs_adds_handler_with_default_log_size_limit():
    truncation_indicator_length = 4
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'Forgetful_buffering_handler'
    ).with_args(
        module.HANDLER_IDENTIFIER,
        module.DEFAULT_LOGS_SIZE_LIMIT_BYTES - truncation_indicator_length,
        1,
    ).once()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('add_handler').once()

    module.initialize_monitor(
        hook_config={},
        config={},
        config_filename='test.yaml',
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_respects_dry_run():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy log')
    mock_apprise().should_receive('notify').never()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}]},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_with_no_states_does_not_notify():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler').never()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).never()
    mock_apprise().should_receive('notify').never()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}], 'states': []},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_notifies_fail_by_default():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic FAIL event happened',
        body='A borgmatic FAIL event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    for state in borgmatic.hooks.monitoring.monitor.State:
        module.ping_monitor(
            {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}]},
            {},
            'config.yaml',
            state,
            monitoring_log_level=1,
            dry_run=False,
        )


def test_ping_monitor_with_logs_appends_logs_to_body():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy log')
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic FAIL event happened',
        body='A borgmatic FAIL event happened\n\nloggy log',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    for state in borgmatic.hooks.monitoring.monitor.State:
        module.ping_monitor(
            {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}]},
            {},
            'config.yaml',
            state,
            monitoring_log_level=1,
            dry_run=False,
        )


def test_ping_monitor_with_finish_default_config_notifies():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic FINISH event happened',
        body='A borgmatic FINISH event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.SUCCESS,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}], 'states': ['finish']},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_start_default_config_notifies():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler').never()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).never()
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic START event happened',
        body='A borgmatic START event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.INFO,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}], 'states': ['start']},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_fail_default_config_notifies():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic FAIL event happened',
        body='A borgmatic FAIL event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}], 'states': ['fail']},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_log_default_config_notifies():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic LOG event happened',
        body='A borgmatic LOG event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.INFO,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}], 'states': ['log']},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_passes_through_custom_message_title():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').with_args(
        title='foo',
        body='bar',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {
            'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}],
            'states': ['fail'],
            'fail': {'title': 'foo', 'body': 'bar'},
        },
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_passes_through_custom_message_body():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').with_args(
        title='',
        body='baz',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {
            'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}],
            'states': ['fail'],
            'fail': {'body': 'baz'},
        },
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_passes_through_custom_message_body_and_appends_logs():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('loggy log')
    mock_apprise().should_receive('notify').with_args(
        title='',
        body='baz\n\nloggy log',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {
            'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}],
            'states': ['fail'],
            'fail': {'body': 'baz'},
        },
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_pings_multiple_services():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('add').with_args([f'ntfys://{TOPIC}', f'ntfy://{TOPIC}']).once()

    module.ping_monitor(
        {
            'services': [
                {'url': f'ntfys://{TOPIC}', 'label': 'ntfys'},
                {'url': f'ntfy://{TOPIC}', 'label': 'ntfy'},
            ]
        },
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_logs_info_for_no_services():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler').never()
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).never()
    flexmock(module.logger).should_receive('info').once()

    module.ping_monitor(
        {'services': []},
        {},
        'config.yaml',
        borgmatic.hooks.monitoring.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_logs_warning_when_notify_fails():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('get_handler')
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive(
        'format_buffered_logs_for_payload'
    ).and_return('')
    mock_apprise().should_receive('notify').and_return(False)
    flexmock(module.logger).should_receive('warning').once()

    for state in borgmatic.hooks.monitoring.monitor.State:
        module.ping_monitor(
            {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}]},
            {},
            'config.yaml',
            state,
            monitoring_log_level=1,
            dry_run=False,
        )


def test_destroy_monitor_does_not_raise():
    flexmock(module.borgmatic.hooks.monitoring.logs).should_receive('remove_handler')

    module.destroy_monitor(
        hook_config={},
        config={},
        config_filename='test.yaml',
        monitoring_log_level=1,
        dry_run=False,
    )
