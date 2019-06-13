import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic.borg import init as module

from ..test_verbosity import insert_logging_mock

INFO_SOME_UNKNOWN_EXIT_CODE = -999
INIT_COMMAND = ('borg', 'init', 'repo', '--encryption', 'repokey')


def insert_info_command_found_mock():
    flexmock(module).should_receive('execute_command')


def insert_info_command_not_found_mock():
    flexmock(module).should_receive('execute_command').and_raise(
        subprocess.CalledProcessError(module.INFO_REPOSITORY_NOT_FOUND_EXIT_CODE, [])
    )


def insert_init_command_mock(init_command, **kwargs):
    flexmock(module.subprocess).should_receive('check_call').with_args(
        init_command, **kwargs
    ).once()


def test_initialize_repository_calls_borg_with_parameters():
    insert_info_command_not_found_mock()
    insert_init_command_mock(INIT_COMMAND)

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_skips_initialization_when_repository_already_exists():
    insert_info_command_found_mock()
    flexmock(module.subprocess).should_receive('check_call').never()

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_raises_for_unknown_info_command_error():
    flexmock(module).should_receive('execute_command').and_raise(
        subprocess.CalledProcessError(INFO_SOME_UNKNOWN_EXIT_CODE, [])
    )

    with pytest.raises(subprocess.CalledProcessError):
        module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_with_append_only_calls_borg_with_append_only_parameter():
    insert_info_command_not_found_mock()
    insert_init_command_mock(INIT_COMMAND + ('--append-only',))

    module.initialize_repository(repository='repo', encryption_mode='repokey', append_only=True)


def test_initialize_repository_with_storage_quota_calls_borg_with_storage_quota_parameter():
    insert_info_command_not_found_mock()
    insert_init_command_mock(INIT_COMMAND + ('--storage-quota', '5G'))

    module.initialize_repository(repository='repo', encryption_mode='repokey', storage_quota='5G')


def test_initialize_repository_with_log_info_calls_borg_with_info_parameter():
    insert_info_command_not_found_mock()
    insert_init_command_mock(INIT_COMMAND + ('--info',))
    insert_logging_mock(logging.INFO)

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_with_log_debug_calls_borg_with_debug_parameter():
    insert_info_command_not_found_mock()
    insert_init_command_mock(INIT_COMMAND + ('--debug',))
    insert_logging_mock(logging.DEBUG)

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_with_local_path_calls_borg_via_local_path():
    insert_info_command_not_found_mock()
    insert_init_command_mock(('borg1',) + INIT_COMMAND[1:])

    module.initialize_repository(repository='repo', encryption_mode='repokey', local_path='borg1')


def test_initialize_repository_with_remote_path_calls_borg_with_remote_path_parameter():
    insert_info_command_not_found_mock()
    insert_init_command_mock(INIT_COMMAND + ('--remote-path', 'borg1'))

    module.initialize_repository(repository='repo', encryption_mode='repokey', remote_path='borg1')
