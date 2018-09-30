import logging

from flexmock import flexmock

from borgmatic.borg import list as module
from ..test_verbosity import insert_logging_mock


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_output').with_args(check_call_command, **kwargs).once()


LIST_COMMAND = ('borg', 'list', 'repo')


def test_list_archives_calls_borg_with_parameters():
    insert_subprocess_mock(LIST_COMMAND)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_info_calls_borg_with_info_parameter():
    insert_subprocess_mock(LIST_COMMAND + ('--info',))
    insert_logging_mock(logging.INFO)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_log_debug_calls_borg_with_debug_parameter():
    insert_subprocess_mock(LIST_COMMAND + ('--debug', '--show-rc'))
    insert_logging_mock(logging.DEBUG)

    module.list_archives(repository='repo', storage_config={})


def test_list_archives_with_json_calls_borg_with_json_parameter():
    insert_subprocess_mock(LIST_COMMAND + ('--json',))

    module.list_archives(repository='repo', storage_config={}, json=True)


def test_list_archives_with_local_path_calls_borg_via_local_path():
    insert_subprocess_mock(('borg1',) + LIST_COMMAND[1:])

    module.list_archives(repository='repo', storage_config={}, local_path='borg1')


def test_list_archives_with_remote_path_calls_borg_with_remote_path_parameters():
    insert_subprocess_mock(LIST_COMMAND + ('--remote-path', 'borg1'))

    module.list_archives(repository='repo', storage_config={}, remote_path='borg1')


def test_list_archives_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    insert_subprocess_mock(LIST_COMMAND + ('--lock-wait', '5'))

    module.list_archives(repository='repo', storage_config=storage_config)
