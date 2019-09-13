import logging

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
        full_command, stderr=module.subprocess.STDOUT, shell=False
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None)

    assert output == expected_output


def test_execute_command_captures_output_with_shell():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, stderr=module.subprocess.STDOUT, shell=True
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None, shell=True)

    assert output == expected_output
