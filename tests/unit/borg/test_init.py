import logging

from flexmock import flexmock

from borgmatic.borg import init as module
from ..test_verbosity import insert_logging_mock


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()


INIT_COMMAND = ('borg', 'init', 'repo', '--encryption', 'repokey')


def test_initialize_repository_calls_borg_with_parameters():
    insert_subprocess_mock(INIT_COMMAND)

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_with_append_only_calls_borg_with_append_only_parameter():
    insert_subprocess_mock(INIT_COMMAND + ('--append-only',))

    module.initialize_repository(repository='repo', encryption_mode='repokey', append_only=True)


def test_initialize_repository_with_storage_quota_calls_borg_with_storage_quota_parameter():
    insert_subprocess_mock(INIT_COMMAND + ('--storage-quota', '5G'))

    module.initialize_repository(repository='repo', encryption_mode='repokey', storage_quota='5G')


def test_initialize_repository_with_log_info_calls_borg_with_info_parameter():
    insert_subprocess_mock(INIT_COMMAND + ('--info',))
    insert_logging_mock(logging.INFO)

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_with_log_debug_calls_borg_with_debug_parameter():
    insert_subprocess_mock(INIT_COMMAND + ('--debug',))
    insert_logging_mock(logging.DEBUG)

    module.initialize_repository(repository='repo', encryption_mode='repokey')


def test_initialize_repository_with_local_path_calls_borg_via_local_path():
    insert_subprocess_mock(('borg1',) + INIT_COMMAND[1:])

    module.initialize_repository(repository='repo', encryption_mode='repokey', local_path='borg1')


def test_initialize_repository_with_remote_path_calls_borg_with_remote_path_parameter():
    insert_subprocess_mock(INIT_COMMAND + ('--remote-path', 'borg1'))

    module.initialize_repository(repository='repo', encryption_mode='repokey', remote_path='borg1')
