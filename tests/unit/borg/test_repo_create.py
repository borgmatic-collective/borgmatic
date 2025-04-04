import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic.borg import repo_create as module

from ..test_verbosity import insert_logging_mock

REPO_INFO_SOME_UNKNOWN_EXIT_CODE = -999
REPO_CREATE_COMMAND = ('borg', 'repo-create', '--encryption', 'repokey')


def insert_repo_info_command_found_mock():
    flexmock(module.repo_info).should_receive('display_repository_info').and_return(
        '{"encryption": {"mode": "repokey"}}'
    )


def insert_repo_info_command_not_found_mock():
    flexmock(module.repo_info).should_receive('display_repository_info').and_raise(
        subprocess.CalledProcessError(
            sorted(module.REPO_INFO_REPOSITORY_NOT_FOUND_EXIT_CODES)[0], []
        )
    )


def insert_repo_create_command_mock(
    repo_create_command, working_directory=None, borg_exit_codes=None, **kwargs
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        repo_create_command,
        output_file=module.DO_NOT_CAPTURE,
        environment=None,
        working_directory=working_directory,
        borg_local_path=repo_create_command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_create_repository_calls_borg_with_flags():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_dry_run_skips_borg_call():
    insert_repo_info_command_not_found_mock()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=True,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_raises_for_borg_repo_create_error():
    insert_repo_info_command_not_found_mock()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').and_raise(
        module.subprocess.CalledProcessError(2, 'borg repo_create')
    )

    with pytest.raises(subprocess.CalledProcessError):
        module.create_repository(
            dry_run=False,
            repository_path='repo',
            config={},
            local_borg_version='2.3.4',
            global_arguments=flexmock(),
            encryption_mode='repokey',
        )


def test_create_repository_skips_creation_when_repository_already_exists():
    insert_repo_info_command_found_mock()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_errors_when_repository_with_differing_encryption_mode_already_exists():
    insert_repo_info_command_found_mock()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    with pytest.raises(ValueError):
        module.create_repository(
            dry_run=False,
            repository_path='repo',
            config={},
            local_borg_version='2.3.4',
            global_arguments=flexmock(),
            encryption_mode='repokey-blake2',
        )


def test_create_repository_raises_for_unknown_repo_info_command_error():
    flexmock(module.repo_info).should_receive('display_repository_info').and_raise(
        subprocess.CalledProcessError(REPO_INFO_SOME_UNKNOWN_EXIT_CODE, [])
    )

    with pytest.raises(subprocess.CalledProcessError):
        module.create_repository(
            dry_run=False,
            repository_path='repo',
            config={},
            local_borg_version='2.3.4',
            global_arguments=flexmock(),
            encryption_mode='repokey',
        )


def test_create_repository_with_source_repository_calls_borg_with_other_repo_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(
        REPO_CREATE_COMMAND + ('--other-repo', 'other.borg', '--repo', 'repo')
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        source_repository='other.borg',
    )


def test_create_repository_with_copy_crypt_key_calls_borg_with_copy_crypt_key_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--copy-crypt-key', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        copy_crypt_key=True,
    )


def test_create_repository_with_append_only_calls_borg_with_append_only_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--append-only', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'append_only': True},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        append_only=True,
    )


def test_create_repository_with_append_only_config_calls_borg_with_append_only_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--append-only', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'append_only': True},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        append_only=True,
    )


def test_create_repository_with_storage_quota_calls_borg_with_storage_quota_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(
        REPO_CREATE_COMMAND + ('--storage-quota', '5G', '--repo', 'repo')
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'storage_quota': '5G'},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        storage_quota='5G',
    )


def test_create_repository_with_make_parent_dirs_calls_borg_with_make_parent_dirs_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--make-parent-dirs', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'make_parent_directories': True},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        make_parent_directories=True,
    )


def test_create_repository_with_log_info_calls_borg_with_info_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--info', '--repo', 'repo'))
    insert_logging_mock(logging.INFO)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_log_debug_calls_borg_with_debug_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--debug', '--repo', 'repo'))
    insert_logging_mock(logging.DEBUG)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_log_json_calls_borg_with_log_json_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--log-json', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'log_json': True},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_lock_wait_calls_borg_with_lock_wait_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--lock-wait', '5', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'lock_wait': 5},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_local_path_calls_borg_via_local_path():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(('borg1',) + REPO_CREATE_COMMAND[1:] + ('--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        local_path='borg1',
    )


def test_create_repository_with_exit_codes_calls_borg_using_them():
    borg_exit_codes = flexmock()
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(
        ('borg',) + REPO_CREATE_COMMAND[1:] + ('--repo', 'repo'), borg_exit_codes=borg_exit_codes
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_remote_path_calls_borg_with_remote_path_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(
        REPO_CREATE_COMMAND + ('--remote-path', 'borg1', '--repo', 'repo')
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
        remote_path='borg1',
    )


def test_create_repository_with_umask_calls_borg_with_umask_flag():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(REPO_CREATE_COMMAND + ('--umask', '077', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'umask': '077'},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_with_extra_borg_options_calls_borg_with_extra_options():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(
        REPO_CREATE_COMMAND + ('--extra', '--options', '--repo', 'repo')
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'extra_borg_options': {'repo-create': '--extra --options'}},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )


def test_create_repository_calls_borg_with_working_directory():
    insert_repo_info_command_not_found_mock()
    insert_repo_create_command_mock(
        REPO_CREATE_COMMAND + ('--repo', 'repo'), working_directory='/working/dir'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(
        (
            '--repo',
            'repo',
        )
    )

    module.create_repository(
        dry_run=False,
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        encryption_mode='repokey',
    )
