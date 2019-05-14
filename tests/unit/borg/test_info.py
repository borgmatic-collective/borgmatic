import logging

from flexmock import flexmock

from borgmatic.borg import info as module

from ..test_verbosity import insert_logging_mock

INFO_COMMAND = ('borg', 'info', 'repo')


def test_display_archives_info_calls_borg_with_parameters():
    flexmock(module).should_receive('execute_command').with_args(INFO_COMMAND, capture_output=False)

    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_info_calls_borg_with_info_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--info',), capture_output=False
    )
    insert_logging_mock(logging.INFO)
    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--debug', '--show-rc'), capture_output=False
    )
    insert_logging_mock(logging.DEBUG)

    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_json_calls_borg_with_json_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--json',), capture_output=True
    ).and_return('[]')

    json_output = module.display_archives_info(repository='repo', storage_config={}, json=True)

    assert json_output == '[]'


def test_display_archives_info_with_local_path_calls_borg_via_local_path():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1',) + INFO_COMMAND[1:], capture_output=False
    )

    module.display_archives_info(repository='repo', storage_config={}, local_path='borg1')


def test_display_archives_info_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--remote-path', 'borg1'), capture_output=False
    )

    module.display_archives_info(repository='repo', storage_config={}, remote_path='borg1')


def test_display_archives_info_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--lock-wait', '5'), capture_output=False
    )

    module.display_archives_info(repository='repo', storage_config=storage_config)
