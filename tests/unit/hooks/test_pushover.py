from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import pushover as module


def test_ping_monitor_config_with_token_only_exit_early():
    # This test should exit early since only providing a token is not enough
    # for the hook to work
    hook_config = {'token': 'ksdjfwoweijfvwoeifvjmwghagy92'}
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_user_only_exit_early():
    # This test should exit early since only providing a token is not enough
    # for the hook to work
    hook_config = {'user': '983hfe0of902lkjfa2amanfgui'}
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_minimum_config_fail_state_backup_successfully_send_to_pushover():
    # This test should be the minimum working configuration. The "message"
    # should be auto populated with the default value which is the state name.
    hook_config = {'token': 'ksdjfwoweijfvwoeifvjmwghagy92', 'user': '983hfe0of902lkjfa2amanfgui'}
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'fail',
        },
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_minimum_config_start_state_backup_not_send_to_pushover_exit_early():
    # This test should exit early since the hook config does not specify the
    # 'start' state. Only the 'fail' state is enabled by default.
    hook_config = {'token': 'ksdjfwoweijfvwoeifvjmwghagy92', 'user': '983hfe0of902lkjfa2amanfgui'}
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_start_state_backup_default_message_successfully_send_to_pushover():
    # This test should send a notification to Pushover on backup start
    # since the state has been configured. It should default to sending
    # the name of the state as the 'message' since it is not
    # explicitly declared in the state config.
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'start',
        },
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_start_state_backup_custom_message_successfully_send_to_pushover():
    # This test should send a notification to Pushover on backup start
    # since the state has been configured. It should send a custom
    # 'message' since it is explicitly declared in the state config.
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {'message': 'custom start message'},
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'custom start message',
        },
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_start_state_backup_default_message_with_priority_declared_successfully_send_to_pushover():
    # This test should send a notification to Pushover on backup start
    # since the state has been configured. It should default to sending
    # the name of the state as the 'message' since it is not
    # explicitly declared in the state config. It should also send
    # with a priority of 1 (high).
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {'priority': 1},
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'start',
            'priority': 1,
        },
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=False,
    )
