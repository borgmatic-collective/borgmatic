import logging

from flexmock import flexmock

from borgmatic.borg import repo_delete as module

from ..test_verbosity import insert_logging_mock


def test_make_repo_delete_command_with_feature_available_runs_borg_repo_delete():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--log-json', 'repo')


def test_make_repo_delete_command_without_feature_available_runs_borg_delete():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--log-json', 'repo')


def test_make_repo_delete_command_includes_log_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--info', '--log-json', 'repo')


def test_make_repo_delete_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--debug', '--show-rc', '--log-json', 'repo')


def test_make_repo_delete_command_includes_dry_run():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'dry-run',
        True,
    ).and_return(('--dry-run',))
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=True),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--dry-run', '--log-json', 'repo')


def test_make_repo_delete_command_includes_remote_path():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'remote-path',
        'borg1',
    ).and_return(('--remote-path', 'borg1'))
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path='borg1',
    )

    assert command == ('borg', 'repo-delete', '--remote-path', 'borg1', '--log-json', 'repo')


def test_make_repo_delete_command_includes_umask():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={'umask': '077'},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--umask', '077', '--log-json', 'repo')


def test_make_repo_delete_command_includes_lock_wait():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'lock-wait',
        5,
    ).and_return(('--lock-wait', '5'))
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={'lock_wait': 5},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--log-json', '--lock-wait', '5', 'repo')


def test_make_repo_delete_command_without_feature_available_includes_delete_extra_borg_options():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={'extra_borg_options': {'delete': '--extra "value with space"'}},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--log-json', '--extra', 'value with space', 'repo')


def test_make_repo_delete_command_with_feature_available_includes_delete_extra_borg_options():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={'extra_borg_options': {'repo_delete': '--extra "value with space"'}},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--log-json', '--extra', 'value with space', 'repo')


def test_make_repo_delete_command_includes_list():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'list',
        True,
    ).and_return(('--list',))
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={'list_details': True},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=True, force=0),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--log-json', '--list', 'repo')


def test_make_repo_delete_command_includes_force():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=1),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--log-json', '--force', 'repo')


def test_make_repo_delete_command_includes_force_twice():
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',),
    )

    command = module.make_repo_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        repo_delete_arguments=flexmock(list_details=False, force=2),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'repo-delete', '--log-json', '--force', '--force', 'repo')


def test_delete_repository_with_defaults_does_not_capture_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    command = flexmock()
    flexmock(module).should_receive('make_repo_delete_command').and_return(command)
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        command,
        output_log_level=module.logging.ANSWER,
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        environment=object,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.delete_repository(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        repo_delete_arguments=flexmock(force=False, cache_only=False),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
    )


def test_delete_repository_with_force_captures_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    command = flexmock()
    flexmock(module).should_receive('make_repo_delete_command').and_return(command)
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        command,
        output_log_level=module.logging.ANSWER,
        output_file=None,
        environment=object,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.delete_repository(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        repo_delete_arguments=flexmock(force=True, cache_only=False),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
    )


def test_delete_repository_with_cache_only_captures_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    command = flexmock()
    flexmock(module).should_receive('make_repo_delete_command').and_return(command)
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        command,
        output_log_level=module.logging.ANSWER,
        output_file=None,
        environment=object,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.delete_repository(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        repo_delete_arguments=flexmock(force=False, cache_only=True),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
    )


def test_delete_repository_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    command = flexmock()
    flexmock(module).should_receive('make_repo_delete_command').and_return(command)
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        command,
        output_log_level=module.logging.ANSWER,
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        environment=object,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.delete_repository(
        repository={'path': 'repo'},
        config={'working_directory': '/working/dir'},
        local_borg_version=flexmock(),
        repo_delete_arguments=flexmock(force=False, cache_only=False),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
    )
