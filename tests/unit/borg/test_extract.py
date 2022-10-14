import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import extract as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, working_directory=None):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command, working_directory=working_directory, extra_environment=None,
    ).once()


def test_extract_last_archive_dry_run_calls_borg_with_last_archive():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', 'repo::archive'))
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        storage_config={}, local_borg_version='1.2.3', repository='repo', lock_wait=None
    )


def test_extract_last_archive_dry_run_without_any_archives_should_not_raise():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_raise(ValueError)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(('repo',))

    module.extract_last_archive_dry_run(
        storage_config={}, local_borg_version='1.2.3', repository='repo', lock_wait=None
    )


def test_extract_last_archive_dry_run_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', '--info', 'repo::archive'))
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        storage_config={}, local_borg_version='1.2.3', repository='repo', lock_wait=None
    )


def test_extract_last_archive_dry_run_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--debug', '--show-rc', '--list', 'repo::archive')
    )
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        storage_config={}, local_borg_version='1.2.3', repository='repo', lock_wait=None
    )


def test_extract_last_archive_dry_run_calls_borg_via_local_path():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg1', 'extract', '--dry-run', 'repo::archive'))
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        storage_config={},
        local_borg_version='1.2.3',
        repository='repo',
        lock_wait=None,
        local_path='borg1',
    )


def test_extract_last_archive_dry_run_calls_borg_with_remote_path_parameters():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--remote-path', 'borg1', 'repo::archive')
    )
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        storage_config={},
        local_borg_version='1.2.3',
        repository='repo',
        lock_wait=None,
        remote_path='borg1',
    )


def test_extract_last_archive_dry_run_calls_borg_with_lock_wait_parameters():
    flexmock(module.rlist).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--lock-wait', '5', 'repo::archive')
    )
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        storage_config={}, local_borg_version='1.2.3', repository='repo', lock_wait=5
    )


def test_extract_archive_calls_borg_with_path_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', 'repo::archive', 'path1', 'path2'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=['path1', 'path2'],
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_extract_archive_calls_borg_with_remote_path_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--remote-path', 'borg1', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
        remote_path='borg1',
    )


@pytest.mark.parametrize(
    'feature_available,option_flag', ((True, '--numeric-ids'), (False, '--numeric-owner'),),
)
def test_extract_archive_calls_borg_with_numeric_ids_parameter(feature_available, option_flag):
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', option_flag, 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(feature_available)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={'numeric_ids': True},
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_extract_archive_calls_borg_with_umask_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--umask', '0770', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={'umask': '0770'},
        local_borg_version='1.2.3',
    )


def test_extract_archive_calls_borg_with_lock_wait_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--lock-wait', '5', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={'lock_wait': '5'},
        local_borg_version='1.2.3',
    )


def test_extract_archive_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--info', 'repo::archive'))
    insert_logging_mock(logging.INFO)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_extract_archive_with_log_debug_calls_borg_with_debug_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'extract', '--debug', '--list', '--show-rc', 'repo::archive')
    )
    insert_logging_mock(logging.DEBUG)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_extract_archive_calls_borg_with_dry_run_parameter():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=True,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_extract_archive_calls_borg_with_destination_path():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', 'repo::archive'), working_directory='/dest')
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
        destination_path='/dest',
    )


def test_extract_archive_calls_borg_with_strip_components():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--strip-components', '5', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
        strip_components=5,
    )


def test_extract_archive_calls_borg_with_progress_parameter():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', '--progress', 'repo::archive'),
        output_file=module.DO_NOT_CAPTURE,
        working_directory=None,
        extra_environment=None,
    ).once()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
        progress=True,
    )


def test_extract_archive_with_progress_and_extract_to_stdout_raises():
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.extract_archive(
            dry_run=False,
            repository='repo',
            archive='archive',
            paths=None,
            location_config={},
            storage_config={},
            local_borg_version='1.2.3',
            progress=True,
            extract_to_stdout=True,
        )


def test_extract_archive_calls_borg_with_stdout_parameter_and_returns_process():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    process = flexmock()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', '--stdout', 'repo::archive'),
        output_file=module.subprocess.PIPE,
        working_directory=None,
        run_to_completion=False,
        extra_environment=None,
    ).and_return(process).once()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    assert (
        module.extract_archive(
            dry_run=False,
            repository='repo',
            archive='archive',
            paths=None,
            location_config={},
            storage_config={},
            local_borg_version='1.2.3',
            extract_to_stdout=True,
        )
        == process
    )


def test_extract_archive_skips_abspath_for_remote_repository():
    flexmock(module.os.path).should_receive('abspath').never()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', 'server:repo::archive'), working_directory=None, extra_environment=None,
    ).once()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('server:repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='server:repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
    )
