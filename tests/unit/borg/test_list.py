import logging

from flexmock import flexmock

from borgmatic.borg import list as module

from ..test_verbosity import insert_logging_mock

LIST_COMMAND = ('borg', 'list', 'repo')


def test_list_archives_calls_borg_with_parameters():
    flexmock(module).should_receive('execute_command').with_args(LIST_COMMAND, capture_output=False)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_info_calls_borg_with_info_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--info',), capture_output=False
    )
    insert_logging_mock(logging.INFO)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--debug', '--show-rc'), capture_output=False
    )
    insert_logging_mock(logging.DEBUG)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--lock-wait', '5'), capture_output=False
    )

    module.list_archives(repository='repo', storage_config=storage_config)


def test_list_archives_with_archive_calls_borg_with_archive_parameter():
    storage_config = {}
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'), capture_output=False
    )

    module.list_archives(repository='repo', storage_config=storage_config, archive='archive')


def test_list_archives_with_local_path_calls_borg_via_local_path():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1',) + LIST_COMMAND[1:], capture_output=False
    )

    module.list_archives(repository='repo', storage_config={}, local_path='borg1')


def test_list_archives_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--remote-path', 'borg1'), capture_output=False
    )

    module.list_archives(repository='repo', storage_config={}, remote_path='borg1')


def test_list_archives_with_json_calls_borg_with_json_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        LIST_COMMAND + ('--json',), capture_output=True
    ).and_return('[]')

    json_output = module.list_archives(repository='repo', storage_config={}, json=True)

    assert json_output == '[]'
