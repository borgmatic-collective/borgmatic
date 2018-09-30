import logging

from flexmock import flexmock

from borgmatic.borg import info as module
from ..test_verbosity import insert_logging_mock


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_output').with_args(check_call_command, **kwargs).once()


INFO_COMMAND = ('borg', 'info', 'repo')


def test_display_archives_info_calls_borg_with_parameters():
    insert_subprocess_mock(INFO_COMMAND)

    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_info_calls_borg_with_info_parameter():
    insert_subprocess_mock(INFO_COMMAND + ('--info',))
    insert_logging_mock(logging.INFO)
    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_log_debug_calls_borg_with_debug_parameter():
    insert_subprocess_mock(INFO_COMMAND + ('--debug', '--show-rc'))
    insert_logging_mock(logging.DEBUG)

    module.display_archives_info(repository='repo', storage_config={})


def test_display_archives_info_with_json_calls_borg_with_json_parameter():
    insert_subprocess_mock(INFO_COMMAND + ('--json',))

    module.display_archives_info(repository='repo', storage_config={}, json=True)


def test_display_archives_info_with_local_path_calls_borg_via_local_path():
    insert_subprocess_mock(('borg1',) + INFO_COMMAND[1:])

    module.display_archives_info(repository='repo', storage_config={}, local_path='borg1')


def test_display_archives_info_with_remote_path_calls_borg_with_remote_path_parameters():
    insert_subprocess_mock(INFO_COMMAND + ('--remote-path', 'borg1'))

    module.display_archives_info(repository='repo', storage_config={}, remote_path='borg1')


def test_display_archives_info_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    insert_subprocess_mock(INFO_COMMAND + ('--lock-wait', '5'))

    module.display_archives_info(repository='repo', storage_config=storage_config)
