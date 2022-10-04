import logging

from flexmock import flexmock

from borgmatic.borg import break_lock as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command, borg_local_path='borg', extra_environment=None,
    ).once()


def test_break_lock_calls_borg_with_required_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', 'repo'))

    module.break_lock(
        repository='repo', storage_config={}, local_borg_version='1.2.3',
    )


def test_break_lock_calls_borg_with_remote_path_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--remote-path', 'borg1', 'repo'))

    module.break_lock(
        repository='repo', storage_config={}, local_borg_version='1.2.3', remote_path='borg1',
    )


def test_break_lock_calls_borg_with_umask_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--umask', '0770', 'repo'))

    module.break_lock(
        repository='repo', storage_config={'umask': '0770'}, local_borg_version='1.2.3',
    )


def test_break_lock_calls_borg_with_lock_wait_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--lock-wait', '5', 'repo'))

    module.break_lock(
        repository='repo', storage_config={'lock_wait': '5'}, local_borg_version='1.2.3',
    )


def test_break_lock_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--info', 'repo'))
    insert_logging_mock(logging.INFO)

    module.break_lock(
        repository='repo', storage_config={}, local_borg_version='1.2.3',
    )


def test_break_lock_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--debug', '--show-rc', 'repo'))
    insert_logging_mock(logging.DEBUG)

    module.break_lock(
        repository='repo', storage_config={}, local_borg_version='1.2.3',
    )
