import logging

from flexmock import flexmock

from borgmatic.borg import borg as module

from ..test_verbosity import insert_logging_mock


def test_run_arbitrary_borg_calls_borg_with_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
    )


def test_run_arbitrary_borg_with_log_info_calls_borg_with_info_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '--info', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.INFO)

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
    )


def test_run_arbitrary_borg_with_log_debug_calls_borg_with_debug_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '--debug', '--show-rc', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.DEBUG)

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
    )


def test_run_arbitrary_borg_with_lock_wait_calls_borg_with_lock_wait_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    config = {'lock_wait': 5}
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(
        ('--lock-wait', '5')
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '--lock-wait', '5', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
    )


def test_run_arbitrary_borg_with_archive_calls_borg_with_archive_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', "'::$ARCHIVE'"),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': 'archive'},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::$ARCHIVE'],
        archive='archive',
    )


def test_run_arbitrary_borg_with_local_path_calls_borg_via_local_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1', 'break-lock', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg1',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
        local_path='borg1',
    )


def test_run_arbitrary_borg_with_exit_codes_calls_borg_using_them():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    borg_exit_codes = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
    )


def test_run_arbitrary_borg_with_remote_path_calls_borg_with_remote_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(
        ('--remote-path', 'borg1')
    ).and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '--remote-path', 'borg1', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
        remote_path='borg1',
    )


def test_run_arbitrary_borg_with_remote_path_injection_attack_gets_escaped():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(
        ('--remote-path', 'borg1; naughty-command')
    ).and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '--remote-path', "'borg1; naughty-command'", '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
        remote_path='borg1',
    )


def test_run_arbitrary_borg_passes_borg_specific_flags_to_borg():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--progress', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['list', '--progress', '::'],
    )


def test_run_arbitrary_borg_omits_dash_dash_in_flags_passed_to_borg():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['--', 'break-lock', '::'],
    )


def test_run_arbitrary_borg_without_borg_specific_flags_does_not_raise():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg',),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=[],
    )


def test_run_arbitrary_borg_passes_key_sub_command_to_borg_before_injected_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'key', 'export', '--info', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.INFO)

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['key', 'export', '::'],
    )


def test_run_arbitrary_borg_passes_debug_sub_command_to_borg_before_injected_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'debug', 'dump-manifest', '--info', '::', 'path'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.INFO)

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['debug', 'dump-manifest', '::', 'path'],
    )


def test_run_arbitrary_borg_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', '::'),
        output_file=module.borgmatic.execute.DO_NOT_CAPTURE,
        shell=True,
        environment={'BORG_REPO': 'repo', 'ARCHIVE': ''},
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.run_arbitrary_borg(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        options=['break-lock', '::'],
    )
