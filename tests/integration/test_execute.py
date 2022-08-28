import logging
import subprocess
import sys

import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_log_outputs_logs_each_line_separately():
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'hi').once()
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'there').once()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    hi_process = subprocess.Popen(['echo', 'hi'], stdout=subprocess.PIPE)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        hi_process, ()
    ).and_return(hi_process.stdout)

    there_process = subprocess.Popen(['echo', 'there'], stdout=subprocess.PIPE)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        there_process, ()
    ).and_return(there_process.stdout)

    module.log_outputs(
        (hi_process, there_process),
        exclude_stdouts=(),
        output_log_level=logging.INFO,
        borg_local_path='borg',
    )


def test_log_outputs_skips_logs_for_process_with_none_stdout():
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'hi').never()
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'there').once()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    hi_process = subprocess.Popen(['echo', 'hi'], stdout=None)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        hi_process, ()
    ).and_return(hi_process.stdout)

    there_process = subprocess.Popen(['echo', 'there'], stdout=subprocess.PIPE)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        there_process, ()
    ).and_return(there_process.stdout)

    module.log_outputs(
        (hi_process, there_process),
        exclude_stdouts=(),
        output_log_level=logging.INFO,
        borg_local_path='borg',
    )


def test_log_outputs_returns_output_without_logging_for_output_log_level_none():
    flexmock(module.logger).should_receive('log').never()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    hi_process = subprocess.Popen(['echo', 'hi'], stdout=subprocess.PIPE)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        hi_process, ()
    ).and_return(hi_process.stdout)

    there_process = subprocess.Popen(['echo', 'there'], stdout=subprocess.PIPE)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        there_process, ()
    ).and_return(there_process.stdout)

    captured_outputs = module.log_outputs(
        (hi_process, there_process),
        exclude_stdouts=(),
        output_log_level=None,
        borg_local_path='borg',
    )

    assert captured_outputs == {hi_process: 'hi', there_process: 'there'}


def test_log_outputs_includes_error_output_in_exception():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('exit_code_indicates_error').and_return(True)
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(['grep'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flexmock(module).should_receive('output_buffer_for_process').and_return(process.stdout)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.log_outputs(
            (process,), exclude_stdouts=(), output_log_level=logging.INFO, borg_local_path='borg'
        )

    assert error.value.output


def test_log_outputs_logs_multiline_error_output():
    '''
    Make sure that all error output lines get logged, not just (for instance) the first few lines
    of a process' traceback.
    '''
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('exit_code_indicates_error').and_return(True)
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(
        ['python', '-c', 'foopydoo'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    flexmock(module).should_receive('output_buffer_for_process').and_return(process.stdout)
    flexmock(module.logger).should_call('log').at_least().times(3)

    with pytest.raises(subprocess.CalledProcessError):
        module.log_outputs(
            (process,), exclude_stdouts=(), output_log_level=logging.INFO, borg_local_path='borg'
        )


def test_log_outputs_skips_error_output_in_exception_for_process_with_none_stdout():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('exit_code_indicates_error').and_return(True)
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(['grep'], stdout=None)
    flexmock(module).should_receive('output_buffer_for_process').and_return(process.stdout)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.log_outputs(
            (process,), exclude_stdouts=(), output_log_level=logging.INFO, borg_local_path='borg'
        )

    assert error.value.returncode == 2
    assert not error.value.output


def test_log_outputs_kills_other_processes_when_one_errors():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(['grep'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flexmock(module).should_receive('exit_code_indicates_error').with_args(
        process, None, 'borg'
    ).and_return(False)
    flexmock(module).should_receive('exit_code_indicates_error').with_args(
        process, 2, 'borg'
    ).and_return(True)
    other_process = subprocess.Popen(
        ['sleep', '2'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    flexmock(module).should_receive('exit_code_indicates_error').with_args(
        other_process, None, 'borg'
    ).and_return(False)
    flexmock(module).should_receive('output_buffer_for_process').with_args(process, ()).and_return(
        process.stdout
    )
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        other_process, ()
    ).and_return(other_process.stdout)
    flexmock(other_process).should_receive('kill').once()

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.log_outputs(
            (process, other_process),
            exclude_stdouts=(),
            output_log_level=logging.INFO,
            borg_local_path='borg',
        )

    assert error.value.returncode == 2
    assert error.value.output


def test_log_outputs_vents_other_processes_when_one_exits():
    '''
    Execute a command to generate a longish random string and pipe it into another command that
    exits quickly. The test is basically to ensure we don't hang forever waiting for the exited
    process to read the pipe, and that the string-generating process eventually gets vented and
    exits.
    '''
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(
        [
            sys.executable,
            '-c',
            "import random, string; print(''.join(random.choice(string.ascii_letters) for _ in range(40000)))",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    other_process = subprocess.Popen(
        ['true'], stdin=process.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        process, (process.stdout,)
    ).and_return(process.stderr)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        other_process, (process.stdout,)
    ).and_return(other_process.stdout)
    flexmock(process.stdout).should_call('readline').at_least().once()

    module.log_outputs(
        (process, other_process),
        exclude_stdouts=(process.stdout,),
        output_log_level=logging.INFO,
        borg_local_path='borg',
    )


def test_log_outputs_does_not_error_when_one_process_exits():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(
        [
            sys.executable,
            '-c',
            "import random, string; print(''.join(random.choice(string.ascii_letters) for _ in range(40000)))",
        ],
        stdout=None,  # Specifically test the case of a process without stdout captured.
        stderr=None,
    )
    other_process = subprocess.Popen(
        ['true'], stdin=process.stdout, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        process, (process.stdout,)
    ).and_return(process.stderr)
    flexmock(module).should_receive('output_buffer_for_process').with_args(
        other_process, (process.stdout,)
    ).and_return(other_process.stdout)

    module.log_outputs(
        (process, other_process),
        exclude_stdouts=(process.stdout,),
        output_log_level=logging.INFO,
        borg_local_path='borg',
    )


def test_log_outputs_truncates_long_error_output():
    flexmock(module).ERROR_OUTPUT_MAX_LINE_COUNT = 0
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('command_for_process').and_return('grep')

    process = subprocess.Popen(['grep'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flexmock(module).should_receive('exit_code_indicates_error').with_args(
        process, None, 'borg'
    ).and_return(False)
    flexmock(module).should_receive('exit_code_indicates_error').with_args(
        process, 2, 'borg'
    ).and_return(True)
    flexmock(module).should_receive('output_buffer_for_process').and_return(process.stdout)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.log_outputs(
            (process,), exclude_stdouts=(), output_log_level=logging.INFO, borg_local_path='borg'
        )

    assert error.value.returncode == 2
    assert error.value.output.startswith('...')


def test_log_outputs_with_no_output_logs_nothing():
    flexmock(module.logger).should_receive('log').never()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    process = subprocess.Popen(['true'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flexmock(module).should_receive('output_buffer_for_process').and_return(process.stdout)

    module.log_outputs(
        (process,), exclude_stdouts=(), output_log_level=logging.INFO, borg_local_path='borg'
    )


def test_log_outputs_with_unfinished_process_re_polls():
    flexmock(module.logger).should_receive('log').never()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    process = subprocess.Popen(['true'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    flexmock(process).should_receive('poll').and_return(None).and_return(0).times(3)
    flexmock(module).should_receive('output_buffer_for_process').and_return(process.stdout)

    module.log_outputs(
        (process,), exclude_stdouts=(), output_log_level=logging.INFO, borg_local_path='borg'
    )
