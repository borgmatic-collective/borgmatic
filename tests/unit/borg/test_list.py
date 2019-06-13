import logging

from flexmock import flexmock

from borgmatic.borg import list as module

from ..test_verbosity import insert_logging_mock

LIST_COMMAND = ('borg', 'list', 'repo')


def test_list_archives_calls_borg_with_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND, output_log_level=logging.WARNING
    )

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_info_calls_borg_with_info_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--info',), output_log_level=logging.WARNING
    )
    insert_logging_mock(logging.INFO)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--json',), output_log_level=None
    )
    insert_logging_mock(logging.INFO)

    module.list_archives(repository='repo', storage_config={}, json=True)


def test_list_archives_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--debug', '--show-rc'), output_log_level=logging.WARNING
    )
    insert_logging_mock(logging.DEBUG)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--json',), output_log_level=None
    )
    insert_logging_mock(logging.DEBUG)

    module.list_archives(repository='repo', storage_config={}, json=True)


def test_list_archives_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--lock-wait', '5'), output_log_level=logging.WARNING
    )

    module.list_archives(repository='repo', storage_config=storage_config)


def test_list_archives_with_archive_calls_borg_with_archive_parameter():
    storage_config = {}
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'), output_log_level=logging.WARNING
    )

    module.list_archives(repository='repo', storage_config=storage_config, archive='archive')


def test_list_archives_with_local_path_calls_borg_via_local_path():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1',) + LIST_COMMAND[1:], output_log_level=logging.WARNING
    )

    module.list_archives(repository='repo', storage_config={}, local_path='borg1')


def test_list_archives_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--remote-path', 'borg1'), output_log_level=logging.WARNING
    )

    module.list_archives(repository='repo', storage_config={}, remote_path='borg1')


def test_list_archives_with_json_calls_borg_with_json_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--json',), output_log_level=None
    ).and_return('[]')

    json_output = module.list_archives(repository='repo', storage_config={}, json=True)

    assert json_output == '[]'
