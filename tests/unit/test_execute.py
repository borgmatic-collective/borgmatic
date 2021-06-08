import subprocess

import pytest
from flexmock import flexmock

from borgmatic import execute as module


@pytest.mark.parametrize(
    'process,exit_code,borg_local_path,expected_result',
    (
        (flexmock(args=['grep']), 2, None, True),
        (flexmock(args=['grep']), 2, 'borg', True),
        (flexmock(args=['borg']), 2, 'borg', True),
        (flexmock(args=['borg1']), 2, 'borg1', True),
        (flexmock(args=['grep']), 1, None, True),
        (flexmock(args=['grep']), 1, 'borg', True),
        (flexmock(args=['borg']), 1, 'borg', False),
        (flexmock(args=['borg1']), 1, 'borg1', False),
        (flexmock(args=['grep']), 0, None, False),
        (flexmock(args=['grep']), 0, 'borg', False),
        (flexmock(args=['borg']), 0, 'borg', False),
        (flexmock(args=['borg1']), 0, 'borg1', False),
        # -9 exit code occurs when child process get SIGKILLed.
        (flexmock(args=['grep']), -9, None, True),
        (flexmock(args=['grep']), -9, 'borg', True),
        (flexmock(args=['borg']), -9, 'borg', True),
        (flexmock(args=['borg1']), -9, 'borg1', True),
        (flexmock(args=['borg']), None, None, False),
    ),
)
def test_exit_code_indicates_error_respects_exit_code_and_borg_local_path(
    process, exit_code, borg_local_path, expected_result
):
    assert module.exit_code_indicates_error(process, exit_code, borg_local_path) is expected_result


def test_command_for_process_converts_sequence_command_to_string():
    process = flexmock(args=['foo', 'bar', 'baz'])

    assert module.command_for_process(process) == 'foo bar baz'


def test_command_for_process_passes_through_string_command():
    process = flexmock(args='foo bar baz')

    assert module.command_for_process(process) == 'foo bar baz'


def test_output_buffer_for_process_returns_stderr_when_stdout_excluded():
    stdout = flexmock()
    stderr = flexmock()
    process = flexmock(stdout=stdout, stderr=stderr)

    assert module.output_buffer_for_process(process, exclude_stdouts=[flexmock(), stdout]) == stderr


def test_output_buffer_for_process_returns_stdout_when_not_excluded():
    stdout = flexmock()
    process = flexmock(stdout=stdout)

    assert (
        module.output_buffer_for_process(process, exclude_stdouts=[flexmock(), flexmock()])
        == stdout
    )


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
    flexmock(module).should_receive('log_outputs')

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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command(full_command, output_file=output_file)

    assert output is None


def test_execute_command_calls_full_command_without_capturing_output():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command, stdin=None, stdout=None, stderr=None, shell=False, env=None, cwd=None
    ).and_return(flexmock(wait=lambda: 0)).once()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command(full_command, output_file=module.DO_NOT_CAPTURE)

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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command(full_command, input_file=input_file)

    assert output is None


def test_execute_command_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        ' '.join(full_command),
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=True,
        env=None,
        cwd=None,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_outputs')

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
    flexmock(module).should_receive('log_outputs')

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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command(full_command, working_directory='/working')

    assert output is None


def test_execute_command_without_run_to_completion_returns_process():
    full_command = ['foo', 'bar']
    process = flexmock()
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=False,
        env=None,
        cwd=None,
    ).and_return(process).once()
    flexmock(module).should_receive('log_outputs')

    assert module.execute_command(full_command, run_to_completion=False) == process


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
        'foo bar', shell=True, env=None, cwd=None
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


def test_execute_command_with_processes_calls_full_command():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(full_command, processes)

    assert output is None


def test_execute_command_with_processes_calls_full_command_with_output_file():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(full_command, processes, output_file=output_file)

    assert output is None


def test_execute_command_with_processes_calls_full_command_without_capturing_output():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command, stdin=None, stdout=None, stderr=None, shell=False, env=None, cwd=None
    ).and_return(flexmock(wait=lambda: 0)).once()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(
        full_command, processes, output_file=module.DO_NOT_CAPTURE
    )

    assert output is None


def test_execute_command_with_processes_calls_full_command_with_input_file():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(full_command, processes, input_file=input_file)

    assert output is None


def test_execute_command_with_processes_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        ' '.join(full_command),
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=True,
        env=None,
        cwd=None,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(full_command, processes, shell=True)

    assert output is None


def test_execute_command_with_processes_calls_full_command_with_extra_environment():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(
        full_command, processes, extra_environment={'c': 'd'}
    )

    assert output is None


def test_execute_command_with_processes_calls_full_command_with_working_directory():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
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
    flexmock(module).should_receive('log_outputs')

    output = module.execute_command_with_processes(
        full_command, processes, working_directory='/working'
    )

    assert output is None


def test_execute_command_with_processes_kills_processes_on_error():
    full_command = ['foo', 'bar']
    process = flexmock(stdout=flexmock(read=lambda count: None))
    process.should_receive('poll')
    process.should_receive('kill').once()
    processes = (process,)
    flexmock(module.os, environ={'a': 'b'})
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.STDOUT,
        shell=False,
        env=None,
        cwd=None,
    ).and_raise(subprocess.CalledProcessError(1, full_command, 'error')).once()
    flexmock(module).should_receive('log_outputs').never()

    with pytest.raises(subprocess.CalledProcessError):
        module.execute_command_with_processes(full_command, processes)
