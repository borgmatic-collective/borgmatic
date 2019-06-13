import logging

from flexmock import flexmock

from borgmatic.borg import info as module

from ..test_verbosity import insert_logging_mock

INFO_COMMAND = ('borg', 'info', 'repo')


def test_display_archives_info_calls_borg_with_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND, output_log_level=logging.WARNING
    )

    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_info_calls_borg_with_info_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--info',), output_log_level=logging.WARNING
    )
    insert_logging_mock(logging.INFO)
    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--json',), output_log_level=None
    ).and_return('[]')

    insert_logging_mock(logging.INFO)
    json_output = module.display_archives_info(repository='repo', storage_config={}, json=True)

    assert json_output == '[]'


def test_display_archives_info_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--debug', '--show-rc'), output_log_level=logging.WARNING
    )
    insert_logging_mock(logging.DEBUG)

    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--json',), output_log_level=None
    ).and_return('[]')

    insert_logging_mock(logging.DEBUG)
    json_output = module.display_archives_info(repository='repo', storage_config={}, json=True)

    assert json_output == '[]'


def test_display_archives_info_with_json_calls_borg_with_json_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--json',), output_log_level=None
    ).and_return('[]')

    json_output = module.display_archives_info(repository='repo', storage_config={}, json=True)

    assert json_output == '[]'


def test_display_archives_info_with_local_path_calls_borg_via_local_path():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1',) + INFO_COMMAND[1:], output_log_level=logging.WARNING
    )

    module.display_archives_info(repository='repo', storage_config={}, local_path='borg1')


def test_display_archives_info_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--remote-path', 'borg1'), output_log_level=logging.WARNING
    )

    module.display_archives_info(repository='repo', storage_config={}, remote_path='borg1')


def test_display_archives_info_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    flexmock(module).should_receive('execute_command').with_args(
        INFO_COMMAND + ('--lock-wait', '5'), output_log_level=logging.WARNING
    )

    module.display_archives_info(repository='repo', storage_config=storage_config)
