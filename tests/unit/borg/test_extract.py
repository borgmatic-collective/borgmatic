import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import extract as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, destination_path=None, borg_exit_codes=None):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command,
        environment=None,
        working_directory=destination_path,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_extract_last_archive_dry_run_calls_borg_with_last_archive():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', 'repo::archive'))
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
    )


def test_extract_last_archive_dry_run_without_any_archives_should_not_raise():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_raise(ValueError)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(('repo',))

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
    )


def test_extract_last_archive_dry_run_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', '--info', 'repo::archive'))
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
    )


def test_extract_last_archive_dry_run_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--debug', '--show-rc', '--list', 'repo::archive')
    )
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
    )


def test_extract_last_archive_dry_run_calls_borg_via_local_path():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg1', 'extract', '--dry-run', 'repo::archive'))
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
        local_path='borg1',
    )


def test_extract_last_archive_dry_run_calls_borg_using_exit_codes():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    borg_exit_codes = flexmock()
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive'), borg_exit_codes=borg_exit_codes
    )
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
    )


def test_extract_last_archive_dry_run_calls_borg_with_remote_path_flags():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--remote-path', 'borg1', 'repo::archive')
    )
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
        remote_path='borg1',
    )


def test_extract_last_archive_dry_run_calls_borg_with_log_json_flag():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', '--log-json', 'repo::archive'))
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={'log_json': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=None,
    )


def test_extract_last_archive_dry_run_calls_borg_with_lock_wait_flags():
    flexmock(module.repo_list).should_receive('resolve_archive_name').and_return('archive')
    insert_execute_command_mock(
        ('borg', 'extract', '--dry-run', '--lock-wait', '5', 'repo::archive')
    )
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_last_archive_dry_run(
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        repository_path='repo',
        lock_wait=5,
    )


def test_extract_archive_calls_borg_with_path_flags():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', 'repo::archive', 'path1', 'path2'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=['path1', 'path2'],
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_local_path():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg1', 'extract', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg1',
    )


def test_extract_archive_calls_borg_with_exit_codes():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    borg_exit_codes = flexmock()
    insert_execute_command_mock(
        ('borg', 'extract', 'repo::archive'), borg_exit_codes=borg_exit_codes
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_remote_path_flags():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--remote-path', 'borg1', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        remote_path='borg1',
    )


@pytest.mark.parametrize(
    'feature_available,option_flag',
    (
        (True, '--numeric-ids'),
        (False, '--numeric-owner'),
    ),
)
def test_extract_archive_calls_borg_with_numeric_ids_parameter(feature_available, option_flag):
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', option_flag, 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(feature_available)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'numeric_ids': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_umask_flags():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--umask', '0770', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'umask': '0770'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_log_json_flags():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--log-json', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'log_json': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_lock_wait_flags():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--lock-wait', '5', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--info', 'repo::archive'))
    insert_logging_mock(logging.INFO)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'extract', '--debug', '--list', '--show-rc', 'repo::archive')
    )
    insert_logging_mock(logging.DEBUG)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_dry_run_parameter():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--dry-run', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=True,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_calls_borg_with_destination_path():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', 'repo::archive'), destination_path='/dest')
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        destination_path='/dest',
    )


def test_extract_archive_calls_borg_with_strip_components():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '--strip-components', '5', 'repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        strip_components=5,
    )


def test_extract_archive_calls_borg_with_strip_components_calculated_from_all():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        (
            'borg',
            'extract',
            '--strip-components',
            '2',
            'repo::archive',
            'foo/bar/baz.txt',
            'foo/bar.txt',
        )
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=['foo/bar/baz.txt', 'foo/bar.txt'],
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        strip_components='all',
    )


def test_extract_archive_calls_borg_with_strip_components_calculated_from_all_with_leading_slash():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        (
            'borg',
            'extract',
            '--strip-components',
            '2',
            'repo::archive',
            '/foo/bar/baz.txt',
            '/foo/bar.txt',
        )
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=['/foo/bar/baz.txt', '/foo/bar.txt'],
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        strip_components='all',
    )


def test_extract_archive_with_strip_components_all_and_no_paths_raises():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.extract_archive(
            dry_run=False,
            repository='repo',
            archive='archive',
            paths=None,
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(),
            strip_components='all',
        )


def test_extract_archive_calls_borg_with_progress_flag():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', '--progress', 'repo::archive'),
        output_file=module.DO_NOT_CAPTURE,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'progress': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_with_progress_and_extract_to_stdout_raises():
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.extract_archive(
            dry_run=False,
            repository='repo',
            archive='archive',
            paths=None,
            config={'progress': True},
            local_borg_version='1.2.3',
            global_arguments=flexmock(),
            extract_to_stdout=True,
        )


def test_extract_archive_calls_borg_with_stdout_parameter_and_returns_process():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    process = flexmock()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', '--stdout', 'repo::archive'),
        output_file=module.subprocess.PIPE,
        run_to_completion=False,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(process).once()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    assert (
        module.extract_archive(
            dry_run=False,
            repository='repo',
            archive='archive',
            paths=None,
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(),
            extract_to_stdout=True,
        )
        == process
    )


def test_extract_archive_skips_abspath_for_remote_repository():
    flexmock(module.os.path).should_receive('abspath').never()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'extract', 'server:repo::archive'),
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('server:repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).and_return('repo')

    module.extract_archive(
        dry_run=False,
        repository='server:repo',
        archive='archive',
        paths=None,
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_extract_archive_uses_configured_working_directory_in_repo_path_and_destination_path():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(
        ('borg', 'extract', '/working/dir/repo::archive'), destination_path='/working/dir/dest'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('/working/dir/repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).with_args('repo', '/working/dir').and_return('/working/dir/repo').once()

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        destination_path='dest',
    )


def test_extract_archive_uses_configured_working_directory_in_repo_path_when_destination_path_is_not_set():
    flexmock(module.os.path).should_receive('abspath').and_return('repo')
    insert_execute_command_mock(('borg', 'extract', '/working/dir/repo::archive'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('/working/dir/repo::archive',)
    )
    flexmock(module.borgmatic.config.validate).should_receive(
        'normalize_repository_path'
    ).with_args('repo', '/working/dir').and_return('/working/dir/repo').once()

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        paths=None,
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )
