import logging

import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_execute_command_calls_full_command():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('execute_and_log_output').with_args(
        full_command, output_log_level=logging.INFO, shell=False
    ).once()

    output = module.execute_command(full_command)

    assert output is None


def test_execute_command_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('execute_and_log_output').with_args(
        full_command, output_log_level=logging.INFO, shell=True
    ).once()

    output = module.execute_command(full_command, shell=True)

    assert output is None


def test_execute_command_captures_output():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=False
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None)

    assert output == expected_output


def test_execute_command_captures_output_with_shell():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=True
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None, shell=True)

    assert output == expected_output


def test_execute_command_without_capture_does_not_raise_on_success():
    flexmock(module.subprocess).should_receive('check_call').and_raise(
        module.subprocess.CalledProcessError(0, 'borg init')
    )

    module.execute_command_without_capture(('borg', 'init'))


def test_execute_command_without_capture_does_not_raise_on_warning():
    flexmock(module.subprocess).should_receive('check_call').and_raise(
        module.subprocess.CalledProcessError(1, 'borg init')
    )

    module.execute_command_without_capture(('borg', 'init'))


def test_execute_command_without_capture_raises_on_error():
    flexmock(module.subprocess).should_receive('check_call').and_raise(
        module.subprocess.CalledProcessError(2, 'borg init')
    )

    with pytest.raises(module.subprocess.CalledProcessError):
        module.execute_command_without_capture(('borg', 'init'))
