import apprise
from apprise import NotifyFormat, NotifyType
from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import apprise as module

TOPIC = 'borgmatic-unit-testing'


def mock_apprise():
    apprise_mock = flexmock(
        add=lambda servers: None, notify=lambda title, body, body_format, notify_type: None
    )
    flexmock(apprise.Apprise).new_instances(apprise_mock)
    return apprise_mock


def test_ping_monitor_adheres_dry_run():
    mock_apprise().should_receive('notify').never()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}]},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_with_no_states():
    mock_apprise().should_receive('notify').never()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}], 'states': []},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_hits_fail_by_default():
    mock_apprise().should_receive('notify').with_args(
        title='A borgmatic FAIL event happened',
        body='A borgmatic FAIL event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    for state in borgmatic.hooks.monitor.State:
        module.ping_monitor(
            {'services': [{'url': f'ntfys://{TOPIC}', 'label': 'ntfys'}]},
            {},
            'config.yaml',
            state,
            monitoring_log_level=1,
            dry_run=False,
        )


def test_ping_monitor_hits_with_finish_default_config():
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
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_with_start_default_config():
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
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_with_fail_default_config():
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
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_with_log_default_config():
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
        borgmatic.hooks.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_passes_through_custom_message_title():
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
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_passes_through_custom_message_body():
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
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_pings_multiple_services():
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
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_warning_for_no_services():
    flexmock(module.logger).should_receive('info').once()

    module.ping_monitor(
        {'services': []},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )
