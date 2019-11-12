import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_exit_code_indicates_error_with_borg_error_is_true():
    assert module.exit_code_indicates_error(('/usr/bin/borg1', 'init'), 2)


def test_exit_code_indicates_error_with_borg_warning_is_false():
    assert not module.exit_code_indicates_error(('/usr/bin/borg1', 'init'), 1)


def test_exit_code_indicates_error_with_borg_success_is_false():
    assert not module.exit_code_indicates_error(('/usr/bin/borg1', 'init'), 0)


def test_exit_code_indicates_error_with_borg_error_and_error_on_warnings_is_true():
    assert module.exit_code_indicates_error(('/usr/bin/borg1', 'init'), 2, error_on_warnings=True)


def test_exit_code_indicates_error_with_borg_warning_and_error_on_warnings_is_true():
    assert module.exit_code_indicates_error(('/usr/bin/borg1', 'init'), 1, error_on_warnings=True)


def test_exit_code_indicates_error_with_borg_success_and_error_on_warnings_is_false():
    assert not module.exit_code_indicates_error(
        ('/usr/bin/borg1', 'init'), 0, error_on_warnings=True
    )


def test_exit_code_indicates_error_with_non_borg_error_is_true():
    assert module.exit_code_indicates_error(('/usr/bin/command',), 2)


def test_exit_code_indicates_error_with_non_borg_warning_is_true():
    assert module.exit_code_indicates_error(('/usr/bin/command',), 1)


def test_exit_code_indicates_error_with_non_borg_success_is_false():
    assert not module.exit_code_indicates_error(('/usr/bin/command',), 0)


def test_execute_command_calls_full_command():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=False,
        env=None,
        cwd=None,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_output')

    output = module.execute_command(full_command)

    assert output is None


def test_execute_command_calls_full_command_with_output_file():
    full_command = ['foo', 'bar']
    output_file = flexmock(name='test')
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=output_file,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
    ).and_return(flexmock(stderr=None)).once()
    flexmock(module).should_receive('log_output')

    output = module.execute_command(full_command, output_file=output_file)

    assert output is None


def test_execute_command_calls_full_command_with_input_file():
    full_command = ['foo', 'bar']
    input_file = flexmock(name='test')
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=input_file,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=False,
        env=None,
        cwd=None,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_output')

    output = module.execute_command(full_command, input_file=input_file)

    assert output is None


def test_execute_command_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=True,
        env=None,
        cwd=None,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_output')

    output = module.execute_command(full_command, shell=True)

    assert output is None


def test_execute_command_calls_full_command_with_extra_environment():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=False,
        env={'a': 'b', 'c': 'd'},
        cwd=None,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_output')

    output = module.execute_command(full_command, extra_environment={'c': 'd'})

    assert output is None


def test_execute_command_calls_full_command_with_working_directory():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=False,
        env=None,
        cwd='/working',
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_output')

    output = module.execute_command(full_command, working_directory='/working')

    assert output is None


def test_execute_command_captures_output():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=False, env=None, cwd=None
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None)

    assert output == expected_output


def test_execute_command_captures_output_with_shell():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=True, env=None, cwd=None
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(full_command, output_log_level=None, shell=True)

    assert output == expected_output


def test_execute_command_captures_output_with_extra_environment():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=False, env={'a': 'b', 'c': 'd'}, cwd=None
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(
        full_command, output_log_level=None, shell=False, extra_environment={'c': 'd'}
    )

    assert output == expected_output


def test_execute_command_captures_output_with_working_directory():
    full_command = ['foo', 'bar']
    expected_output = '[]'
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('check_output').with_args(
        full_command, shell=False, env=None, cwd='/working'
    ).and_return(flexmock(decode=lambda: expected_output)).once()

    output = module.execute_command(
        full_command, output_log_level=None, shell=False, working_directory='/working'
    )

    assert output == expected_output


def test_execute_command_without_capture_does_not_raise_on_success():
    flexmock(module.subprocess).should_receive('check_call').and_raise(
        module.subprocess.CalledProcessError(0, 'borg init')
    )

    module.execute_command_without_capture(('borg', 'init'))


def test_execute_command_without_capture_does_not_raise_on_warning():
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)
    flexmock(module.subprocess).should_receive('check_call').and_raise(
        module.subprocess.CalledProcessError(1, 'borg init')
    )

    module.execute_command_without_capture(('borg', 'init'))


def test_execute_command_without_capture_raises_on_error():
    flexmock(module).should_receive('exit_code_indicates_error').and_return(True)
    flexmock(module.subprocess).should_receive('check_call').and_raise(
        module.subprocess.CalledProcessError(2, 'borg init')
    )

    with pytest.raises(module.subprocess.CalledProcessError):
        module.execute_command_without_capture(('borg', 'init'))
