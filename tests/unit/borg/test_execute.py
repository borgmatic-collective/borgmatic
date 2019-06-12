import logging

from flexmock import flexmock

from borgmatic.borg import execute as module


def test_execute_command_calls_full_command():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('execute_and_log_output').with_args(
        full_command, output_log_level=logging.INFO
    ).once()

    output = module.execute_command(full_command)

    assert output is None


def test_execute_command_captures_output():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.subprocess).should_receive('check_output').with_args(full_command).and_return(
        flexmock(decode=lambda: expected_output)
    ).once()

    output = module.execute_command(full_command, output_log_level=None)

    assert output == expected_output
