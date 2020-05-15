import logging

from flexmock import flexmock

from borgmatic.borg import umount as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command):
    flexmock(module).should_receive('execute_command').with_args(command).once()


def test_unmount_archive_calls_borg_with_required_parameters():
    insert_execute_command_mock(('borg', 'umount', '/mnt'))

    module.unmount_archive(mount_point='/mnt')


def test_unmount_archive_with_log_info_calls_borg_with_info_parameter():
    insert_execute_command_mock(('borg', 'umount', '--info', '/mnt'))
    insert_logging_mock(logging.INFO)

    module.unmount_archive(mount_point='/mnt')


def test_unmount_archive_with_log_debug_calls_borg_with_debug_parameters():
    insert_execute_command_mock(('borg', 'umount', '--debug', '--show-rc', '/mnt'))
    insert_logging_mock(logging.DEBUG)

    module.unmount_archive(mount_point='/mnt')
