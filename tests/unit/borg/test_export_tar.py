import logging

from flexmock import flexmock

from borgmatic.borg import export_tar as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    command,
    output_log_level=logging.INFO,
    working_directory=None,
    borg_local_path='borg',
    borg_exit_codes=None,
    capture=True,
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        command,
        output_file=None if capture else module.DO_NOT_CAPTURE,
        output_log_level=output_log_level,
        environment=None,
        working_directory=working_directory,
        borg_local_path=borg_local_path,
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_export_tar_archive_calls_borg_with_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', 'repo::archive', 'test.tar', 'path1', 'path2')
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=['path1', 'path2'],
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_local_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg1', 'export-tar', 'repo::archive', 'test.tar'), borg_local_path='borg1'
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg1',
    )


def test_export_tar_archive_calls_borg_using_exit_codes():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    borg_exit_codes = flexmock()
    insert_execute_command_mock(
        ('borg', 'export-tar', 'repo::archive', 'test.tar'),
        borg_exit_codes=borg_exit_codes,
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_remote_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--remote-path', 'borg1', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        remote_path='borg1',
    )


def test_export_tar_archive_calls_borg_with_umask_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--umask', '0770', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={'umask': '0770'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_log_json_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'export-tar', '--log-json', 'repo::archive', 'test.tar'))

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={'log_json': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_lock_wait_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--lock-wait', '5', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_with_log_info_calls_borg_with_info_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'export-tar', '--info', 'repo::archive', 'test.tar'))
    insert_logging_mock(logging.INFO)

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--debug', '--show-rc', 'repo::archive', 'test.tar')
    )
    insert_logging_mock(logging.DEBUG)

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_dry_run_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('execute_command').never()

    module.export_tar_archive(
        dry_run=True,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_tar_filter_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--tar-filter', 'bzip2', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        tar_filter='bzip2',
    )


def test_export_tar_archive_calls_borg_with_list_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--list', 'repo::archive', 'test.tar'),
        output_log_level=logging.ANSWER,
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={'list_details': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_strip_components_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', '--strip-components', '5', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        strip_components=5,
    )


def test_export_tar_archive_skips_abspath_for_remote_repository_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('server:repo::archive',)
    )
    insert_execute_command_mock(('borg', 'export-tar', 'server:repo::archive', 'test.tar'))

    module.export_tar_archive(
        dry_run=False,
        repository_path='server:repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_stdout_destination_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'export-tar', 'repo::archive', '-'), capture=False)

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=None,
        destination_path='-',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_export_tar_archive_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'export-tar', 'repo::archive', 'test.tar'),
        working_directory='/working/dir',
    )

    module.export_tar_archive(
        dry_run=False,
        repository_path='repo',
        archive='archive',
        paths=[],
        destination_path='test.tar',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )
