import logging

from flexmock import flexmock

from borgmatic.borg import umount as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    command, borg_local_path='borg', working_directory=None, borg_exit_codes=None
):
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        command,
        working_directory=working_directory,
        borg_local_path=borg_local_path,
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_unmount_archive_calls_borg_with_required_parameters():
    insert_execute_command_mock(('borg', 'umount', '/mnt'))

    module.unmount_archive(config={}, mount_point='/mnt')


def test_unmount_archive_with_log_info_calls_borg_with_info_parameter():
    insert_execute_command_mock(('borg', 'umount', '--info', '/mnt'))
    insert_logging_mock(logging.INFO)

    module.unmount_archive(config={}, mount_point='/mnt')


def test_unmount_archive_with_log_debug_calls_borg_with_debug_parameters():
    insert_execute_command_mock(('borg', 'umount', '--debug', '--show-rc', '/mnt'))
    insert_logging_mock(logging.DEBUG)

    module.unmount_archive(config={}, mount_point='/mnt')


def test_unmount_archive_calls_borg_with_local_path():
    insert_execute_command_mock(('borg1', 'umount', '/mnt'), borg_local_path='borg1')

    module.unmount_archive(config={}, mount_point='/mnt', local_path='borg1')


def test_unmount_archive_calls_borg_with_exit_codes():
    borg_exit_codes = flexmock()
    insert_execute_command_mock(('borg', 'umount', '/mnt'), borg_exit_codes=borg_exit_codes)

    module.unmount_archive(config={'borg_exit_codes': borg_exit_codes}, mount_point='/mnt')


def test_unmount_archive_calls_borg_with_working_directory():
    insert_execute_command_mock(('borg', 'umount', '/mnt'), working_directory='/working/dir')

    module.unmount_archive(config={'working_directory': '/working/dir'}, mount_point='/mnt')
