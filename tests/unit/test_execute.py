import logging

import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_execute_command_calls_full_command():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module).should_receive('execute_and_log_output').with_args(
        full_command, output_log_level=logging.INFO, shell=False, environment=None
    ).once()

    output = module.execute_command(full_command)

    assert output is None


def test_execute_command_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module).should_receive('execute_and_log_output').with_args(
        full_command, output_log_level=logging.INFO, shell=True, environment=None
    ).once()

    output = module.execute_command(full_command, shell=True)

    assert output is None


def test_execute_command_calls_full_command_with_extra_environment():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module).should_receive('execute_and_log_output').with_args(
        full_command, output_log_level=logging.INFO, shell=False, environment={'a': 'b', 'c': 'd'}
    ).once()

    output = module.execute_command(full_command, extra_environment={'c': 'd'})

    assert output is None


def test_execute_command_captures_output():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=False, env=None
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None)

    assert output == expected_output


def test_execute_command_captures_output_with_shell():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=True, env=None
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None, shell=True)

    assert output == expected_output


def test_execute_command_captures_output_with_extra_environment():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=False, env={'a': 'b', 'c': 'd'}
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(
        full_command, output_log_level=None, shell=False, extra_environment={'c': 'd'}
    )

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
