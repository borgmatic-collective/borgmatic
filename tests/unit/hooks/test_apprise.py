import apprise
from apprise import NotifyFormat, NotifyType
from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import apprise as module

topic = 'borgmatic-unit-testing'


def test_ping_monitor_adheres_dry_run():
    flexmock(apprise.Apprise).should_receive('notify').never()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}]},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_does_not_hit_with_no_states():
    flexmock(apprise.Apprise).should_receive('notify').never()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}], 'states': []},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_hits_fail_by_default():
    flexmock(apprise.Apprise).should_receive('notify').once()

    for state in borgmatic.hooks.monitor.State:
        module.ping_monitor(
            {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}]},
            {},
            'config.yaml',
            state,
            monitoring_log_level=1,
            dry_run=False,
        )


def test_ping_monitor_hits_with_finish_default_config():
    flexmock(apprise.Apprise).should_receive('notify').with_args(
        title='A borgmatic FINISH event happened',
        body='A borgmatic FINISH event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.SUCCESS,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}], 'states': ['finish']},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_with_start_default_config():
    flexmock(apprise.Apprise).should_receive('notify').with_args(
        title='A borgmatic START event happened',
        body='A borgmatic START event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.INFO,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}], 'states': ['start']},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_with_fail_default_config():
    flexmock(apprise.Apprise).should_receive('notify').with_args(
        title='A borgmatic FAIL event happened',
        body='A borgmatic FAIL event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}], 'states': ['fail']},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_hits_with_log_default_config():
    flexmock(apprise.Apprise).should_receive('notify').with_args(
        title='A borgmatic LOG event happened',
        body='A borgmatic LOG event happened',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.INFO,
    ).once()

    module.ping_monitor(
        {'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}], 'states': ['log']},
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.LOG,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_custom_message_title():
    flexmock(apprise.Apprise).should_receive('notify').with_args(
        title='foo',
        body='bar',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {
            'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}],
            'states': ['fail'],
            'fail': {'title': 'foo', 'body': 'bar'},
        },
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_with_custom_message_body():
    flexmock(apprise.Apprise).should_receive('notify').with_args(
        title='',
        body='baz',
        body_format=NotifyFormat.TEXT,
        notify_type=NotifyType.FAILURE,
    ).once()

    module.ping_monitor(
        {
            'services': [{'url': f'ntfys://{topic}', 'label': 'ntfys'}],
            'states': ['fail'],
            'fail': {'body': 'baz'},
        },
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_multiple_services():
    flexmock(apprise.Apprise).should_receive('add').with_args(
        [f'ntfys://{topic}', f'ntfy://{topic}']
    ).once()

    module.ping_monitor(
        {
            'services': [
                {'url': f'ntfys://{topic}', 'label': 'ntfys'},
                {'url': f'ntfy://{topic}', 'label': 'ntfy'},
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
