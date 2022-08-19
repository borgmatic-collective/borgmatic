import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic.borg import rcreate as module

from ..test_verbosity import insert_logging_mock

RINFO_SOME_UNKNOWN_EXIT_CODE = -999
RCREATE_COMMAND = ('borg', 'rcreate', '--encryption', 'repokey')


def insert_rinfo_command_found_mock():
    flexmock(module.rinfo).should_receive('display_repository_info')


def insert_rinfo_command_not_found_mock():
    flexmock(module.rinfo).should_receive('display_repository_info').and_raise(
        subprocess.CalledProcessError(module.RINFO_REPOSITORY_NOT_FOUND_EXIT_CODE, [])
    )


def insert_rcreate_command_mock(rcreate_command, **kwargs):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        rcreate_command,
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path=rcreate_command[0],
        extra_environment=None,
    ).once()


def test_create_repository_calls_borg_with_flags():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
    )


def test_create_repository_with_dry_run_skips_borg_call():
    insert_rinfo_command_not_found_mock()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=True,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
    )


def test_create_repository_raises_for_borg_rcreate_error():
    insert_rinfo_command_not_found_mock()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').and_raise(
        module.subprocess.CalledProcessError(2, 'borg rcreate')
    )

    with pytest.raises(subprocess.CalledProcessError):
        module.create_repository(
            dry_run=False,
            repository='repo',
            storage_config={},
            local_borg_version='2.3.4',
            encryption_mode='repokey',
        )


def test_create_repository_skips_creation_when_repository_already_exists():
    insert_rinfo_command_found_mock()
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
    )


def test_create_repository_raises_for_unknown_rinfo_command_error():
    flexmock(module.rinfo).should_receive('display_repository_info').and_raise(
        subprocess.CalledProcessError(RINFO_SOME_UNKNOWN_EXIT_CODE, [])
    )

    with pytest.raises(subprocess.CalledProcessError):
        module.create_repository(
            dry_run=False,
            repository='repo',
            storage_config={},
            local_borg_version='2.3.4',
            encryption_mode='repokey',
        )


def test_create_repository_with_source_repository_calls_borg_with_other_repo_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--other-repo', 'other.borg', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        source_repository='other.borg',
    )


def test_create_repository_with_copy_crypt_key_calls_borg_with_copy_crypt_key_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--copy-crypt-key', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        copy_crypt_key=True,
    )


def test_create_repository_with_append_only_calls_borg_with_append_only_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--append-only', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        append_only=True,
    )


def test_create_repository_with_storage_quota_calls_borg_with_storage_quota_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--storage-quota', '5G', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        storage_quota='5G',
    )


def test_create_repository_with_make_parent_dirs_calls_borg_with_make_parent_dirs_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--make-parent-dirs', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        make_parent_dirs=True,
    )


def test_create_repository_with_log_info_calls_borg_with_info_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--info', '--repo', 'repo'))
    insert_logging_mock(logging.INFO)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
    )


def test_create_repository_with_log_debug_calls_borg_with_debug_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--debug', '--repo', 'repo'))
    insert_logging_mock(logging.DEBUG)
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
    )


def test_create_repository_with_local_path_calls_borg_via_local_path():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(('borg1',) + RCREATE_COMMAND[1:] + ('--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        local_path='borg1',
    )


def test_create_repository_with_remote_path_calls_borg_with_remote_path_flag():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--remote-path', 'borg1', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
        remote_path='borg1',
    )


def test_create_repository_with_extra_borg_options_calls_borg_with_extra_options():
    insert_rinfo_command_not_found_mock()
    insert_rcreate_command_mock(RCREATE_COMMAND + ('--extra', '--options', '--repo', 'repo'))
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))

    module.create_repository(
        dry_run=False,
        repository='repo',
        storage_config={'extra_borg_options': {'rcreate': '--extra --options'}},
        local_borg_version='2.3.4',
        encryption_mode='repokey',
    )
