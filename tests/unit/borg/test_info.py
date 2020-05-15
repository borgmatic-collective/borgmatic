import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import info as module

from ..test_verbosity import insert_logging_mock


def test_display_archives_info_calls_borg_with_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg'
    )

    module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive=None, json=False)
    )


def test_display_archives_info_with_log_info_calls_borg_with_info_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--info', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg'
    )
    insert_logging_mock(logging.INFO)
    module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive=None, json=False)
    )


def test_display_archives_info_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--json', 'repo'), output_log_level=None, borg_local_path='borg'
    ).and_return('[]')

    insert_logging_mock(logging.INFO)
    json_output = module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive=None, json=True)
    )

    assert json_output == '[]'


def test_display_archives_info_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--debug', '--show-rc', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )
    insert_logging_mock(logging.DEBUG)

    module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive=None, json=False)
    )


def test_display_archives_info_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--json', 'repo'), output_log_level=None, borg_local_path='borg'
    ).and_return('[]')

    insert_logging_mock(logging.DEBUG)
    json_output = module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive=None, json=True)
    )

    assert json_output == '[]'


def test_display_archives_info_with_json_calls_borg_with_json_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--json', 'repo'), output_log_level=None, borg_local_path='borg'
    ).and_return('[]')

    json_output = module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive=None, json=True)
    )

    assert json_output == '[]'


def test_display_archives_info_with_archive_calls_borg_with_archive_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', 'repo::archive'), output_log_level=logging.WARNING, borg_local_path='borg'
    )

    module.display_archives_info(
        repository='repo', storage_config={}, info_arguments=flexmock(archive='archive', json=False)
    )


def test_display_archives_info_with_local_path_calls_borg_via_local_path():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1', 'info', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg1'
    )

    module.display_archives_info(
        repository='repo',
        storage_config={},
        info_arguments=flexmock(archive=None, json=False),
        local_path='borg1',
    )


def test_display_archives_info_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--remote-path', 'borg1', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.display_archives_info(
        repository='repo',
        storage_config={},
        info_arguments=flexmock(archive=None, json=False),
        remote_path='borg1',
    )


def test_display_archives_info_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--lock-wait', '5', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.display_archives_info(
        repository='repo',
        storage_config=storage_config,
        info_arguments=flexmock(archive=None, json=False),
    )


@pytest.mark.parametrize('argument_name', ('prefix', 'glob_archives', 'sort_by', 'first', 'last'))
def test_display_archives_info_passes_through_arguments_to_borg(argument_name):
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--' + argument_name.replace('_', '-'), 'value', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.display_archives_info(
        repository='repo',
        storage_config={},
        info_arguments=flexmock(archive=None, json=False, **{argument_name: 'value'}),
    )
