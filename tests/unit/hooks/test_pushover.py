from flexmock import flexmock

import borgmatic.hooks.monitor
from borgmatic.hooks import pushover as module


def test_ping_monitor_config_with_minimum_config_fail_state_backup_successfully_send_to_pushover():
    '''
    This test should be the minimum working configuration. The "message"
    should be auto populated with the default value which is the state name.
    '''
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
    '''
    This test should exit early since the hook config does not specify the
    'start' state. Only the 'fail' state is enabled by default.
    '''
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
    '''
    This test should send a notification to Pushover on backup start
    since the state has been configured. It should default to sending
    the name of the state as the 'message' since it is not
    explicitly declared in the state config.
    '''
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
    '''
    This test should send a notification to Pushover on backup start
    since the state has been configured. It should send a custom
    'message' since it is explicitly declared in the state config.
    '''
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


def test_ping_monitor_start_state_backup_default_message_with_priority_emergency_uses_expire_and_retry_defaults():
    '''
    This simulates priority level 2 being set but expiry and retry are
    not declared. This should set retry and expiry to their defaults.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {'priority': 2},
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'start',
            'priority': 2,
            'retry': 30,
            'expire': 600,
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


def test_ping_monitor_start_state_backup_default_message_with_priority_emergency_declared_with_expire_no_retry_success():
    '''
    This simulates priority level 2 and expiry being set but retry is
    not declared. This should set retry to the default.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {'priority': 2, 'expire': 600},
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'start',
            'priority': 2,
            'retry': 30,
            'expire': 600,
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


def test_ping_monitor_start_state_backup_default_message_with_priority_emergency_declared_no_expire_with_retry_success():
    '''
    This simulates priority level 2  and retry being set but expire is
    not declared. This should set expire to the default.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {'priority': 2, 'retry': 30},
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'start',
            'priority': 2,
            'retry': 30,
            'expire': 600,
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


def test_ping_monitor_start_state_backup_default_message_with_priority_high_declared_expire_and_retry_delared_success():
    '''
    This simulates priority level 1, retry and expiry being set. Since expire
    and retry are only used for priority level 2, they should not be included
    in the request sent to Pushover. This test verifies that those are
    stripped from the request.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {'priority': 1, 'expire': 30, 'retry': 30},
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


def test_ping_monitor_start_state_backup_based_on_documentation_advanced_example_success():
    '''
    Here is a test of what is provided in the monitor-your-backups.md file
    as an 'advanced example'. This test runs the start state.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {
            'message': 'Backup <b>Started</b>',
            'priority': -2,
            'title': 'Backup Started',
            'html': 1,
            'ttl': 10,
        },
        'fail': {
            'message': 'Backup <font color="#ff6961">Failed</font>',
            'priority': 2,
            'expire': 600,
            'retry': 30,
            'device': 'pixel8',
            'title': 'Backup Failed',
            'html': 1,
            'sound': 'siren',
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
        'finish': {
            'message': 'Backup <font color="#77dd77">Finished</font>',
            'priority': 0,
            'title': 'Backup Finished',
            'html': 1,
            'ttl': 60,
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'Backup <b>Started</b>',
            'priority': -2,
            'title': 'Backup Started',
            'html': 1,
            'ttl': 10,
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


def test_ping_monitor_fail_state_backup_based_on_documentation_advanced_example_success():
    '''
    Here is a test of what is provided in the monitor-your-backups.md file
    as an 'advanced example'. This test runs the fail state.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {
            'message': 'Backup <b>Started</b>',
            'priority': -2,
            'title': 'Backup Started',
            'html': 1,
            'ttl': 10,
        },
        'fail': {
            'message': 'Backup <font color="#ff6961">Failed</font>',
            'priority': 2,
            'expire': 600,
            'retry': 30,
            'device': 'pixel8',
            'title': 'Backup Failed',
            'html': 1,
            'sound': 'siren',
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
        'finish': {
            'message': 'Backup <font color="#77dd77">Finished</font>',
            'priority': 0,
            'title': 'Backup Finished',
            'html': 1,
            'ttl': 60,
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'Backup <font color="#ff6961">Failed</font>',
            'priority': 2,
            'expire': 600,
            'retry': 30,
            'device': 'pixel8',
            'title': 'Backup Failed',
            'html': 1,
            'sound': 'siren',
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
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


def test_ping_monitor_finish_state_backup_based_on_documentation_advanced_example_success():
    '''
    Here is a test of what is provided in the monitor-your-backups.md file
    as an 'advanced example'. This test runs the finish state.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
        'states': {'start', 'fail', 'finish'},
        'start': {
            'message': 'Backup <b>Started</b>',
            'priority': -2,
            'title': 'Backup Started',
            'html': 1,
            'ttl': 10,
        },
        'fail': {
            'message': 'Backup <font color="#ff6961">Failed</font>',
            'priority': 2,
            'expire': 600,
            'retry': 30,
            'device': 'pixel8',
            'title': 'Backup Failed',
            'html': 1,
            'sound': 'siren',
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
        'finish': {
            'message': 'Backup <font color="#77dd77">Finished</font>',
            'priority': 0,
            'title': 'Backup Finished',
            'html': 1,
            'ttl': 60,
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
    }
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module.requests).should_receive('post').with_args(
        'https://api.pushover.net/1/messages.json',
        headers={'Content-type': 'application/x-www-form-urlencoded'},
        data={
            'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
            'user': '983hfe0of902lkjfa2amanfgui',
            'message': 'Backup <font color="#77dd77">Finished</font>',
            'priority': 0,
            'title': 'Backup Finished',
            'html': 1,
            'ttl': 60,
            'url': 'https://ticketing-system.example.com/login',
            'url_title': 'Login to ticketing system',
        },
    ).and_return(flexmock(ok=True)).once()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FINISH,
        monitoring_log_level=1,
        dry_run=False,
    )


def test_ping_monitor_config_with_minimum_config_fail_state_backup_successfully_send_to_pushover_dryrun():
    '''
    This test should be the minimum working configuration. The "message"
    should be auto populated with the default value which is the state name.
    '''
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
    ).and_return(flexmock(ok=True)).never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.FAIL,
        monitoring_log_level=1,
        dry_run=True,
    )


def test_ping_monitor_config_incorrect_state_exit_early():
    '''
    This test should exit early since the start state is not declared in the configuration.
    '''
    hook_config = {
        'token': 'ksdjfwoweijfvwoeifvjmwghagy92',
        'user': '983hfe0of902lkjfa2amanfgui',
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
    ).and_return(flexmock(ok=True)).never()

    module.ping_monitor(
        hook_config,
        {},
        'config.yaml',
        borgmatic.hooks.monitor.State.START,
        monitoring_log_level=1,
        dry_run=True,
    )
