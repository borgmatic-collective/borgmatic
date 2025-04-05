import logging

from flexmock import flexmock

from borgmatic.borg import break_lock as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, working_directory=None, borg_exit_codes=None):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        command,
        environment=None,
        working_directory=working_directory,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_break_lock_calls_borg_with_required_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_break_lock_calls_borg_with_local_path():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1', 'break-lock', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg1',
    )


def test_break_lock_calls_borg_using_exit_codes():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1', 'break-lock', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg1',
    )


def test_break_lock_calls_borg_with_remote_path_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--remote-path', 'borg1', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        remote_path='borg1',
    )


def test_break_lock_calls_borg_with_umask_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--umask', '0770', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={'umask': '0770'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_break_lock_calls_borg_with_log_json_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--log-json', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={'log_json': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_break_lock_calls_borg_with_lock_wait_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--lock-wait', '5', 'repo'))

    module.break_lock(
        repository_path='repo',
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_break_lock_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--info', 'repo'))
    insert_logging_mock(logging.INFO)

    module.break_lock(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_break_lock_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', '--debug', '--show-rc', 'repo'))
    insert_logging_mock(logging.DEBUG)

    module.break_lock(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_break_lock_calls_borg_with_working_directory():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'break-lock', 'repo'), working_directory='/working/dir')

    module.break_lock(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )
