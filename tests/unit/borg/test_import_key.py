import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import import_key as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    command,
    working_directory=None,
    borg_exit_codes=None,
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        command,
        output_log_level=module.logging.INFO,
        environment=None,
        working_directory=working_directory,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_import_key_calls_borg_with_required_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'import', '--log-json', 'repo', '-'))

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_local_path():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg1', 'key', 'import', '--log-json', 'repo', '-'))

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg1',
    )


def test_import_key_calls_borg_using_exit_codes():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    borg_exit_codes = flexmock()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', 'repo', '-'), borg_exit_codes=borg_exit_codes
    )

    module.import_key(
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_remote_path_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--remote-path', 'borg1', '--log-json', 'repo', '-')
    )

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
        remote_path='borg1',
    )


def test_import_key_calls_borg_with_umask_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--umask', '0770', '--log-json', 'repo', '-')
    )

    module.import_key(
        repository_path='repo',
        config={'umask': '0770'},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_lock_wait_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', '--lock-wait', '5', 'repo', '-')
    )

    module.import_key(
        repository_path='repo',
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_extra_borg_options():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', '--extra', 'value with space', 'repo', '-')
    )

    module.import_key(
        repository_path='repo',
        config={'extra_borg_options': {'key_import': '--extra "value with space"'}},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'import', '--log-json', '--info', 'repo', '-'))
    insert_logging_mock(logging.INFO)

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', '--debug', '--show-rc', 'repo', '-')
    )
    insert_logging_mock(logging.DEBUG)

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_paper_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(('--paper',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'import', '--log-json', '--paper', 'repo', '-'))

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=True, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_path_argument():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').with_args('source').and_return(True)
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', 'repo', 'source'),
    )

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path='source'),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_with_non_existent_path_raises():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.import_key(
            repository_path='repo',
            config={},
            local_borg_version='1.2.3',
            import_arguments=flexmock(paper=False, path='source'),
            global_arguments=flexmock(dry_run=False),
        )


def test_import_key_with_stdin_path_calls_borg_without_path_argument():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'import', '--log-json', 'repo', '-'))

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path='-'),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_with_dry_run_skips_borg_call():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module).should_receive('execute_command').never()

    module.import_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=True),
    )


def test_import_key_calls_borg_with_working_directory():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', 'repo', '-'), working_directory='/working/dir'
    )

    module.import_key(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path=None),
        global_arguments=flexmock(dry_run=False),
    )


def test_import_key_calls_borg_with_path_argument_and_working_directory():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').with_args('/working/dir/source').and_return(
        True,
    ).once()
    insert_execute_command_mock(
        ('borg', 'key', 'import', '--log-json', 'repo', 'source'),
        working_directory='/working/dir',
    )

    module.import_key(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        import_arguments=flexmock(paper=False, path='source'),
        global_arguments=flexmock(dry_run=False),
    )
