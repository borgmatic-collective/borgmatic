import logging

from flexmock import flexmock

from borgmatic.borg import mount as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command):
    flexmock(module).should_receive('execute_command').with_args(
        command, borg_local_path='borg'
    ).once()


def test_mount_archive_calls_borg_with_required_parameters():
    insert_execute_command_mock(('borg', 'mount', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={},
    )


def test_mount_archive_calls_borg_with_path_parameters():
    insert_execute_command_mock(('borg', 'mount', 'repo::archive', '/mnt', 'path1', 'path2'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=['path1', 'path2'],
        foreground=False,
        options=None,
        storage_config={},
    )


def test_mount_archive_calls_borg_with_remote_path_parameters():
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
        remote_path='borg1',
    )


def test_mount_archive_calls_borg_with_umask_parameters():
    insert_execute_command_mock(('borg', 'mount', '--umask', '0770', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={'umask': '0770'},
    )


def test_mount_archive_calls_borg_with_lock_wait_parameters():
    insert_execute_command_mock(('borg', 'mount', '--lock-wait', '5', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options=None,
        storage_config={'lock_wait': '5'},
    )


def test_mount_archive_with_log_info_calls_borg_with_info_parameter():
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
    )


def test_mount_archive_with_log_debug_calls_borg_with_debug_parameters():
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
    )


def test_mount_archive_calls_borg_with_foreground_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'mount', '--foreground', 'repo::archive', '/mnt'),
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path='borg',
    ).once()

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=True,
        options=None,
        storage_config={},
    )


def test_mount_archive_calls_borg_with_options_parameters():
    insert_execute_command_mock(('borg', 'mount', '-o', 'super_mount', 'repo::archive', '/mnt'))

    module.mount_archive(
        repository='repo',
        archive='archive',
        mount_point='/mnt',
        paths=None,
        foreground=False,
        options='super_mount',
        storage_config={},
    )
