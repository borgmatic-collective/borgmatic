import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import extract as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, working_directory=None):
    flexmock(module).should_receive('execute_command').with_args(
        command, working_directory=working_directory
    ).once()


def insert_execute_command_output_mock(command, result):
    flexmock(module).should_receive('execute_command').with_args(
        command, output_log_level=None, borg_local_path=command[0]
    ).and_return(result).once()


def test_extract_last_archive_dry_run_calls_borg_with_last_archive():
    insert_execute_command_output_mock(
        ('borg', 'list', '--short', 'repo'), result='archive1\narchive2\n'
    )
    insert_execute_command_mock(('borg', 'extract', '--dry-run', 'repo::archive2'))
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_without_any_archives_should_not_raise():
    insert_execute_command_output_mock(('borg', 'list', '--short', 'repo'), result='\n')
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_with_log_info_calls_borg_with_info_parameter():
    insert_execute_command_output_mock(
        ('borg', 'list', '--short', '--info', 'repo'), result='archive1\narchive2\n'
    )
    insert_execute_command_mock(('borg', 'extract', '--dry-run', '--info', 'repo::archive2'))
    insert_logging_mock(logging.INFO)
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_with_log_debug_calls_borg_with_debug_parameter():
    insert_execute_command_output_mock(
        ('borg', 'list', '--short', '--debug', '--show-rc', 'repo'), result='archive1\narchive2\n'
    )
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--debug', '--show-rc', '--list', 'repo::archive2')
    )
    insert_logging_mock(logging.DEBUG)
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_calls_borg_via_local_path():
    insert_execute_command_output_mock(
        ('borg1', 'list', '--short', 'repo'), result='archive1\narchive2\n'
    )
    insert_execute_command_mock(('borg1', 'extract', '--dry-run', 'repo::archive2'))
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None, local_path='borg1')


def test_extract_last_archive_dry_run_calls_borg_with_remote_path_parameters():
    insert_execute_command_output_mock(
        ('borg', 'list', '--short', '--remote-path', 'borg1', 'repo'), result='archive1\narchive2\n'
    )
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--remote-path', 'borg1', 'repo::archive2')
    )
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None, remote_path='borg1')


def test_extract_last_archive_dry_run_calls_borg_with_lock_wait_parameters():
    insert_execute_command_output_mock(
        ('borg', 'list', '--short', '--lock-wait', '5', 'repo'), result='archive1\narchive2\n'
    )
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--lock-wait', '5', 'repo::archive2')
    )
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=5)


def test_extract_archive_calls_borg_with_path_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', 'repo::archive', 'path1', 'path2'))
    flexmock(module.feature).should_receive('available').and_return(True)

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

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        location_config={'numeric_owner': True},
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_extract_archive_calls_borg_with_umask_parameters():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--umask', '0770', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)

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
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', '--progress', 'repo::archive'),
        output_file=module.DO_NOT_CAPTURE,
        working_directory=None,
    ).once()
    flexmock(module.feature).should_receive('available').and_return(True)

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
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', '--stdout', 'repo::archive'),
        output_file=module.subprocess.PIPE,
        working_directory=None,
        run_to_completion=False,
    ).and_return(process).once()
    flexmock(module.feature).should_receive('available').and_return(True)

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
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', 'server:repo::archive'), working_directory=None
    ).once()
    flexmock(module.feature).should_receive('available').and_return(True)

    module.extract_archive(
        dry_run=False,
        repository='server:repo',
        archive='archive',
        paths=None,
        location_config={},
        storage_config={},
        local_borg_version='1.2.3',
    )
