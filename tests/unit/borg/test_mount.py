import logging

from flexmock import flexmock

from borgmatic.borg import mount as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command, borg_local_path='borg', extra_environment=None,
    ).once()


def test_mount_archive_calls_borg_with_required_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'mount', 'repo', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive=None,
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_with_borg_features_calls_borg_with_repository_and_match_archives_flags():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo',))
    insert_execute_command_mock(
        ('borg', 'mount', '--repo', 'repo', '--match-archives', 'archive', '/mnt')
    )

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_without_archive_calls_borg_with_repository_flags_only():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_calls_borg_with_path_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', 'repo::archive', '/mnt', 'path1', 'path2'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=['path1', 'path2'],
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_calls_borg_with_remote_path_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(
        ('borg', 'mount', '--remote-path', 'borg1', 'repo::archive', '/mnt')
    )

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
        remote_path='borg1',
    )


def test_mount_archive_calls_borg_with_umask_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', '--umask', '0770', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={'umask': '0770'},
        local_borg_version='1.2.3',
    )


def test_mount_archive_calls_borg_with_lock_wait_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', '--lock-wait', '5', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={'lock_wait': '5'},
        local_borg_version='1.2.3',
    )


def test_mount_archive_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', '--info', 'repo::archive', '/mnt'))
    insert_logging_mock(logging.INFO)

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', '--debug', '--show-rc', 'repo::archive', '/mnt'))
    insert_logging_mock(logging.DEBUG)

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_calls_borg_with_foreground_parameter():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'mount', '--foreground', 'repo::archive', '/mnt'),
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path='borg',
        extra_environment=None,
    ).once()

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=True,
        options=None,
        storage_config={},
        local_borg_version='1.2.3',
    )


def test_mount_archive_calls_borg_with_options_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )
    insert_execute_command_mock(('borg', 'mount', '-o', 'super_mount', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options='super_mount',
        storage_config={},
        local_borg_version='1.2.3',
    )
