import logging

from flexmock import flexmock

from borgmatic.borg import repo_info as module

from ..test_verbosity import insert_logging_mock


def test_display_repository_info_calls_borg_with_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_without_borg_features_calls_borg_with_info_sub_command():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--log-json', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_with_log_info_calls_borg_with_info_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--info', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.INFO)
    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags').never()

    insert_logging_mock(logging.INFO)
    json_output = module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=True),
        global_arguments=flexmock(),
    )

    assert json_output == '[]'


def test_display_repository_info_with_log_debug_calls_borg_with_debug_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--debug', '--show-rc', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--debug', '--show-rc', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.DEBUG)

    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags').never()

    insert_logging_mock(logging.DEBUG)
    json_output = module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=True),
        global_arguments=flexmock(),
    )

    assert json_output == '[]'


def test_display_repository_info_with_json_calls_borg_with_json_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags').never()

    json_output = module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=True),
        global_arguments=flexmock(),
    )

    assert json_output == '[]'


def test_display_repository_info_with_local_path_calls_borg_via_local_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg1', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1', 'repo-info', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg1',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
        local_path='borg1',
    )


def test_display_repository_info_with_exit_codes_calls_borg_using_them():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    borg_exit_codes = flexmock()
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
    )

    module.display_repository_info(
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_with_remote_path_calls_borg_with_remote_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--remote-path', 'borg1', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--remote-path', 'borg1', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
        remote_path='borg1',
    )


def test_display_repository_info_with_umask_calls_borg_with_umask_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--umask', '077', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--umask', '077', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config={'umask': '077'},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
        remote_path=None,
    )


def test_display_repository_info_with_lock_wait_calls_borg_with_lock_wait_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    config = {'lock_wait': 5}
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', str(value)) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--lock-wait', '5', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--log-json', '--lock-wait', '5', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config=config,
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_without_feature_available_calls_borg_with_info_extra_borg_options():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    config = {'extra_borg_options': {'info': '--extra "value with space"'}}
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', str(value)) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'info', '--log-json', '--extra', 'value with space', '--json', '--repo', 'repo'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--log-json', '--extra', 'value with space', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config=config,
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_with_feature_available_calls_borg_with_repo_info_extra_borg_options():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    config = {'extra_borg_options': {'repo_info': '--extra "value with space"'}}
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', str(value)) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'borg',
            'repo-info',
            '--log-json',
            '--extra',
            'value with space',
            '--json',
            '--repo',
            'repo',
        ),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--log-json', '--extra', 'value with space', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config=config,
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )


def test_display_repository_info_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else (),
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        ),
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-info', '--log-json', '--json', '--repo', 'repo'),
        environment=None,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_yield('[]')
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'repo-info', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        environment=None,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.display_repository_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        repo_info_arguments=flexmock(json=False),
        global_arguments=flexmock(),
    )
