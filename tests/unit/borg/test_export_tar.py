import logging

from flexmock import flexmock

from borgmatic.borg import export_tar as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    command, output_log_level=logging.INFO, borg_local_path='borg', capture=True
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command,
        output_file=None if capture else module.DO_NOT_CAPTURE,
        output_log_level=output_log_level,
        borg_local_path=borg_local_path,
        extra_environment=None,
    ).once()


def test_export_tar_archive_calls_borg_with_path_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', 'repo::archive', 'test.tar', 'path1', 'path2')
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=['path1', 'path2'],
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_calls_borg_with_local_path_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg1', 'export-tar', 'repo::archive', 'test.tar'), borg_local_path='borg1'
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
        local_path='borg1',
    )


def test_export_tar_archive_calls_borg_with_remote_path_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--remote-path', 'borg1', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
        remote_path='borg1',
    )


def test_export_tar_archive_calls_borg_with_umask_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--umask', '0770', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={'umask': '0770'},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_calls_borg_with_lock_wait_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--lock-wait', '5', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={'lock_wait': '5'},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'export-tar', '--info', 'repo::archive', 'test.tar'))
    insert_logging_mock(logging.INFO)

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_with_log_debug_calls_borg_with_debug_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--debug', '--show-rc', 'repo::archive', 'test.tar')
    )
    insert_logging_mock(logging.DEBUG)

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_calls_borg_with_dry_run_parameter():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    flexmock(module).should_receive('execute_command').never()

    module.export_tar_archive(
        dry_run=True,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_calls_borg_with_tar_filter_parameters():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--tar-filter', 'bzip2', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
        tar_filter='bzip2',
    )


def test_export_tar_archive_calls_borg_with_list_parameter():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--list', 'repo::archive', 'test.tar'),
        output_log_level=logging.WARNING,
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
        list_files=True,
    )


def test_export_tar_archive_calls_borg_with_strip_components_parameter():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'export-tar', '--strip-components', '5', 'repo::archive', 'test.tar')
    )

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
        strip_components=5,
    )


def test_export_tar_archive_skips_abspath_for_remote_repository_parameter():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('server:repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').never()
    insert_execute_command_mock(('borg', 'export-tar', 'server:repo::archive', 'test.tar'))

    module.export_tar_archive(
        dry_run=False,
        repository='server:repo',
        archive='archive',
        paths=None,
        destination_path='test.tar',
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_export_tar_archive_calls_borg_with_stdout_destination_path():
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'export-tar', 'repo::archive', '-'), capture=False)

    module.export_tar_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        destination_path='-',
        storage_config={},
        local_borg_version='1.2.3',
    )
