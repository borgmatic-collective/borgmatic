import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import version as module

from ..test_verbosity import insert_logging_mock

VERSION = '1.2.3'


def insert_execute_command_mock(command, borg_local_path='borg', version_output=f'borg {VERSION}'):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command, output_log_level=None, borg_local_path=borg_local_path, extra_environment=None,
    ).once().and_return(version_output)


def test_local_borg_version_calls_borg_with_required_parameters():
    insert_execute_command_mock(('borg', '--version'))
    flexmock(module.environment).should_receive('make_environment')

    assert module.local_borg_version({}) == VERSION


def test_local_borg_version_with_log_info_calls_borg_with_info_parameter():
    insert_execute_command_mock(('borg', '--version', '--info'))
    insert_logging_mock(logging.INFO)
    flexmock(module.environment).should_receive('make_environment')

    assert module.local_borg_version({}) == VERSION


def test_local_borg_version_with_log_debug_calls_borg_with_debug_parameters():
    insert_execute_command_mock(('borg', '--version', '--debug', '--show-rc'))
    insert_logging_mock(logging.DEBUG)
    flexmock(module.environment).should_receive('make_environment')

    assert module.local_borg_version({}) == VERSION


def test_local_borg_version_with_local_borg_path_calls_borg_with_it():
    insert_execute_command_mock(('borg1', '--version'), borg_local_path='borg1')
    flexmock(module.environment).should_receive('make_environment')

    assert module.local_borg_version({}, 'borg1') == VERSION


def test_local_borg_version_with_invalid_version_raises():
    insert_execute_command_mock(('borg', '--version'), version_output='wtf')
    flexmock(module.environment).should_receive('make_environment')

    with pytest.raises(ValueError):
        module.local_borg_version({})
