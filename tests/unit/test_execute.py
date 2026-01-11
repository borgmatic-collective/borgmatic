import subprocess

import pytest
from flexmock import flexmock

from borgmatic import execute as module


@pytest.mark.parametrize(
    'command,exit_code,borg_local_path,borg_exit_codes,expected_result',
    (
        (['grep'], 2, None, None, module.Exit_status.ERROR),
        (['grep'], 2, 'borg', None, module.Exit_status.ERROR),
        (['borg'], 2, 'borg', None, module.Exit_status.ERROR),
        (['borg1'], 2, 'borg1', None, module.Exit_status.ERROR),
        (['grep'], 1, None, None, module.Exit_status.ERROR),
        (['grep'], 1, 'borg', None, module.Exit_status.ERROR),
        (['borg'], 1, 'borg', None, module.Exit_status.WARNING),
        (['borg1'], 1, 'borg1', None, module.Exit_status.WARNING),
        (['grep'], 100, None, None, module.Exit_status.ERROR),
        (['grep'], 100, 'borg', None, module.Exit_status.ERROR),
        (['borg'], 100, 'borg', None, module.Exit_status.WARNING),
        (['borg1'], 100, 'borg1', None, module.Exit_status.WARNING),
        (['grep'], 0, None, None, module.Exit_status.SUCCESS),
        (['grep'], 0, 'borg', None, module.Exit_status.SUCCESS),
        (['borg'], 0, 'borg', None, module.Exit_status.SUCCESS),
        (['borg1'], 0, 'borg1', None, module.Exit_status.SUCCESS),
        # -9 exit code occurs when child process get SIGKILLed.
        (['grep'], -9, None, None, module.Exit_status.ERROR),
        (['grep'], -9, 'borg', None, module.Exit_status.ERROR),
        (['borg'], -9, 'borg', None, module.Exit_status.ERROR),
        (['borg1'], -9, 'borg1', None, module.Exit_status.ERROR),
        (['borg'], None, None, None, module.Exit_status.STILL_RUNNING),
        (['borg'], 1, 'borg', [], module.Exit_status.WARNING),
        (['borg'], 1, 'borg', [{}], module.Exit_status.WARNING),
        (['borg'], 1, 'borg', [{'code': 1}], module.Exit_status.WARNING),
        (['grep'], 1, 'borg', [{'code': 100, 'treat_as': 'error'}], module.Exit_status.ERROR),
        (['borg'], 1, 'borg', [{'code': 100, 'treat_as': 'error'}], module.Exit_status.WARNING),
        (['borg'], 1, 'borg', [{'code': 1, 'treat_as': 'error'}], module.Exit_status.ERROR),
        (['borg'], 2, 'borg', [{'code': 99, 'treat_as': 'warning'}], module.Exit_status.ERROR),
        (['borg'], 2, 'borg', [{'code': 2, 'treat_as': 'warning'}], module.Exit_status.WARNING),
        (['borg'], 100, 'borg', [{'code': 1, 'treat_as': 'error'}], module.Exit_status.WARNING),
        (['borg'], 100, 'borg', [], module.Exit_status.WARNING),
        (['borg'], 100, 'borg', [{'code': 100, 'treat_as': 'error'}], module.Exit_status.ERROR),
        (['borg'], 101, 'borg', [], module.Exit_status.ERROR),
        (['borg'], 101, 'borg', [{'code': 101, 'treat_as': 'warning'}], module.Exit_status.WARNING),
        (['borg'], 102, 'borg', [], module.Exit_status.ERROR),
        (['borg'], 102, 'borg', [{'code': 102, 'treat_as': 'warning'}], module.Exit_status.WARNING),
        (['borg'], 103, 'borg', [], module.Exit_status.WARNING),
        (['borg'], 103, 'borg', [{'code': 103, 'treat_as': 'error'}], module.Exit_status.ERROR),
        (['borg'], 104, 'borg', [], module.Exit_status.ERROR),
        (['borg'], 104, 'borg', [{'code': 104, 'treat_as': 'warning'}], module.Exit_status.WARNING),
        (['borg'], 105, 'borg', [], module.Exit_status.ERROR),
        (['borg'], 105, 'borg', [{'code': 105, 'treat_as': 'warning'}], module.Exit_status.WARNING),
        (['borg'], 106, 'borg', [], module.Exit_status.ERROR),
        (['borg'], 106, 'borg', [{'code': 106, 'treat_as': 'warning'}], module.Exit_status.WARNING),
        (['borg'], 107, 'borg', [], module.Exit_status.ERROR),
        (['borg'], 107, 'borg', [{'code': 107, 'treat_as': 'warning'}], module.Exit_status.WARNING),
    ),
)
def test_interpret_exit_code_respects_exit_code_and_borg_local_path(
    command,
    exit_code,
    borg_local_path,
    borg_exit_codes,
    expected_result,
):
    assert (
        module.interpret_exit_code(command, exit_code, borg_local_path, borg_exit_codes)
        is expected_result
    )


def test_command_for_process_converts_sequence_command_to_string():
    process = flexmock(args=['foo', 'bar', 'baz'])

    assert module.command_for_process(process) == 'foo bar baz'


def test_command_for_process_passes_through_string_command():
    process = flexmock(args='foo bar baz')

    assert module.command_for_process(process) == 'foo bar baz'


def test_output_buffers_for_process_returns_stdout_and_stderr_by_default():
    stdout = flexmock()
    stderr = flexmock()
    process = flexmock(stdout=stdout, stderr=stderr)

    assert module.output_buffers_for_process(process, exclude_stdouts=[flexmock(), flexmock()]) == (
        stdout,
        stderr,
    )


def test_output_buffers_for_process_returns_stderr_only_when_stdout_excluded():
    stdout = flexmock()
    stderr = flexmock()
    process = flexmock(stdout=stdout, stderr=stderr)

    assert module.output_buffers_for_process(process, exclude_stdouts=[flexmock(), stdout]) == (
        stderr,
    )


def test_borg_log_line_to_record_parses_line():
    flexmock(module).should_receive('log_line_to_record').never()
    line = '{"levelname": "INFO", "time": 12345, "message": "All done", "name": "borg.something"}'

    record = module.borg_log_line_to_record(line, module.logging.INFO)

    assert record.levelno == module.logging.INFO
    assert record.created == 12345
    assert record.msg == 'All done'
    assert record.levelname == 'INFO'
    assert record.name == 'borg.something'


def test_borg_log_line_to_record_with_invalid_json_falls_back_to_raw_line():
    record = flexmock()
    line = '{invalid'
    flexmock(module).should_receive('log_line_to_record').with_args(
        line, module.logging.INFO
    ).and_return(record).once()

    assert module.borg_log_line_to_record(line, module.logging.INFO) == record


def test_borg_log_line_to_record_with_non_dict_json_falls_back_to_raw_line():
    record = flexmock()
    line = '[]'
    flexmock(module).should_receive('log_line_to_record').with_args(
        line, module.logging.INFO
    ).and_return(record).once()

    assert module.borg_log_line_to_record(line, module.logging.INFO) == record


def test_log_line_to_record_makes_log_record():
    line = 'All done'

    record = module.log_line_to_record(line, module.logging.INFO)

    assert record.msg == line
    assert record.levelno == module.logging.INFO
    assert record.levelname == 'INFO'


def test_parse_log_line_with_borg_command_parses_borg_log_line():
    record = flexmock()
    flexmock(module).should_receive('borg_log_line_to_record').and_return(record).once()
    flexmock(module).should_receive('log_line_to_record').never()

    assert (
        module.parse_log_line(
            'All done',
            module.logging.INFO,
            came_from_stderr=False,
            borg_local_path='borg',
            command=['borg', 'do-stuff'],
        )
        == record
    )


def test_parse_log_line_without_borg_command_parses_plain_log_line():
    record = flexmock()
    flexmock(module).should_receive('borg_log_line_to_record').never()
    flexmock(module).should_receive('log_line_to_record').and_return(record).once()

    assert (
        module.parse_log_line(
            'All done',
            module.logging.INFO,
            came_from_stderr=False,
            borg_local_path='borg',
            command=['totally-not-borg', 'do-stuff'],
        )
        == record
    )


def test_parse_log_line_with_came_from_stderr_makes_error_record():
    record = flexmock()
    flexmock(module).should_receive('borg_log_line_to_record').never()
    flexmock(module).should_receive('log_line_to_record').with_args(
        'All done', module.logging.ERROR
    ).and_return(record).once()

    assert (
        module.parse_log_line(
            'All done',
            module.logging.INFO,
            came_from_stderr=True,
            borg_local_path='borg',
            command=['totally-not-borg', 'do-stuff'],
        )
        == record
    )


def test_parse_log_line_with_came_from_stderr_and_warning_prefix_makes_warning_record():
    record = flexmock()
    flexmock(module).should_receive('borg_log_line_to_record').never()
    flexmock(module).should_receive('log_line_to_record').with_args(
        'warning: All done', module.logging.WARNING
    ).and_return(record).once()

    assert (
        module.parse_log_line(
            'warning: All done',
            module.logging.INFO,
            came_from_stderr=True,
            borg_local_path='borg',
            command=['totally-not-borg', 'do-stuff'],
        )
        == record
    )


def test_handle_log_record_under_max_line_count_appends():
    last_lines = ['last']
    flexmock(module.logger).should_receive('handle').once()
    log_record = flexmock(levelno=module.logging.INFO, getMessage=lambda: 'line')

    assert (
        module.handle_log_record(
            log_record,
            last_lines,
        )
        == log_record
    )

    assert last_lines == ['last', 'line']


def test_handle_log_record_over_max_line_count_trims_and_appends():
    original_last_lines = [str(number) for number in range(module.ERROR_OUTPUT_MAX_LINE_COUNT)]
    last_lines = list(original_last_lines)
    flexmock(module.logger).should_receive('handle').once()
    log_record = flexmock(levelno=module.logging.INFO, getMessage=lambda: 'line')

    assert (
        module.handle_log_record(
            log_record,
            last_lines,
        )
        == log_record
    )

    assert last_lines == [*original_last_lines[1:], 'line']


def test_mask_command_secrets_masks_password_flag_value():
    assert module.mask_command_secrets(('cooldb', '--username', 'bob', '--password', 'pass')) == (
        'cooldb',
        '--username',
        'bob',
        '--password',
        '***',
    )


def test_mask_command_secrets_passes_through_other_commands():
    assert module.mask_command_secrets(('cooldb', '--username', 'bob')) == (
        'cooldb',
        '--username',
        'bob',
    )


@pytest.mark.parametrize(
    'full_command,input_file,output_file,environment,expected_result',
    (
        (('foo', 'bar'), None, None, None, 'foo bar'),
        (('foo', 'bar'), flexmock(name='input'), None, None, 'foo bar < input'),
        (('foo', 'bar'), None, flexmock(name='output'), None, 'foo bar > output'),
        (
            ('A',) * module.MAX_LOGGED_COMMAND_LENGTH,
            None,
            None,
            None,
            'A ' * (module.MAX_LOGGED_COMMAND_LENGTH // 2 - 2) + '...',
        ),
        (
            ('foo', 'bar'),
            flexmock(name='input'),
            flexmock(name='output'),
            None,
            'foo bar < input > output',
        ),
        (
            ('foo', 'bar'),
            None,
            None,
            {'UNKNOWN': 'secret', 'OTHER': 'thing'},
            'foo bar',
        ),
        (
            ('foo', 'bar'),
            None,
            None,
            {'PGTHING': 'secret', 'BORG_OTHER': 'thing'},
            'PGTHING=*** BORG_OTHER=*** foo bar',
        ),
    ),
)
def test_log_command_logs_command_constructed_from_arguments(
    full_command,
    input_file,
    output_file,
    environment,
    expected_result,
):
    flexmock(module).should_receive('mask_command_secrets').replace_with(lambda command: command)
    flexmock(module.logger).should_receive('debug').with_args(expected_result).once()

    module.log_command(full_command, input_file, output_file, environment)


def test_execute_command_calls_full_command():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command)

    assert output is None


def test_execute_command_calls_full_command_with_output_file():
    full_command = ['foo', 'bar']
    output_file = flexmock(name='test')
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=output_file,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stderr=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command, output_file=output_file)

    assert output is None


def test_execute_command_calls_full_command_without_capturing_output():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=None,
        stderr=None,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(wait=lambda: 0)).once()
    flexmock(module).should_receive('interpret_exit_code').and_return(module.Exit_status.SUCCESS)
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command, output_file=module.DO_NOT_CAPTURE)

    assert output is None


def test_execute_command_calls_full_command_with_input_file():
    full_command = ['foo', 'bar']
    input_file = flexmock(name='test')
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=input_file,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command, input_file=input_file)

    assert output is None


def test_execute_command_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        ' '.join(full_command),
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=True,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command, shell=True)

    assert output is None


def test_execute_command_calls_full_command_with_environment():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env={'a': 'b'},
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command, environment={'a': 'b'})

    assert output is None


def test_execute_command_calls_full_command_with_working_directory():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd='/working',
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output = module.execute_command(full_command, working_directory='/working')

    assert output is None


def test_execute_command_without_run_to_completion_returns_process():
    full_command = ['foo', 'bar']
    process = flexmock()
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    assert module.execute_command(full_command, run_to_completion=False) == process


def test_execute_command_and_capture_output_returns_stdout():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    process = flexmock()
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield('out')

    output_lines = tuple(module.execute_command_and_capture_output(full_command))

    assert output_lines == ('out',)


def test_execute_command_and_capture_output_with_capture_stderr_returns_stderr():
    full_command = ['foo', 'bar']
    process = flexmock()
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield('out')

    output_lines = tuple(
        module.execute_command_and_capture_output(full_command, capture_stderr=True)
    )

    assert output_lines == ('out',)


def test_execute_command_and_capture_output_returns_output_when_process_error_is_not_considered_an_error():
    full_command = ['foo', 'bar']
    err_output = b'[]'
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_raise(subprocess.CalledProcessError(1, full_command, err_output)).once()
    flexmock(module).should_receive('interpret_exit_code').and_return(
        module.Exit_status.SUCCESS,
    ).once()

    output_lines = tuple(module.execute_command_and_capture_output(full_command))

    assert output_lines == ('[]',)


def test_execute_command_and_capture_output_raises_when_command_errors():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_raise(subprocess.CalledProcessError(2, full_command, 'error')).once()
    flexmock(module).should_receive('interpret_exit_code').and_return(
        module.Exit_status.ERROR,
    ).once()

    with pytest.raises(subprocess.CalledProcessError):
        tuple(module.execute_command_and_capture_output(full_command))


def test_execute_command_and_capture_output_with_shell_returns_output():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    process = flexmock()
    flexmock(module.subprocess).should_receive('Popen').with_args(
        'foo bar',
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield('out')

    output_lines = tuple(module.execute_command_and_capture_output(full_command, shell=True))

    assert output_lines == ('out',)


def test_execute_command_and_capture_output_with_enviroment_returns_output():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    process = flexmock()
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env={'a': 'b'},
        cwd=None,
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield('out')

    output_lines = tuple(
        module.execute_command_and_capture_output(
            full_command,
            shell=False,
            environment={'a': 'b'},
        )
    )

    assert output_lines == ('out',)


def test_execute_command_and_capture_output_returns_output_with_working_directory():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    process = flexmock()
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        env=None,
        cwd='/working',
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield('out')

    output_lines = tuple(
        module.execute_command_and_capture_output(
            full_command,
            shell=False,
            working_directory='/working',
        )
    )

    assert output_lines == ('out',)


def test_execute_command_with_processes_calls_full_command():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(module.execute_command_with_processes(full_command, processes))

    assert output_lines == ()


def test_execute_command_with_processes_returns_output_with_output_log_level_none():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module).should_receive('log_command')
    process = flexmock(stdout=None)
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(process).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield('out')

    output_lines = tuple(
        module.execute_command_with_processes(full_command, processes, output_log_level=None)
    )

    assert output_lines == ('out',)


def test_execute_command_with_processes_calls_full_command_with_output_file():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    output_file = flexmock(name='test')
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=output_file,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stderr=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(
        module.execute_command_with_processes(full_command, processes, output_file=output_file)
    )

    assert output_lines == ()


def test_execute_command_with_processes_calls_full_command_without_capturing_output():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=None,
        stderr=None,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(wait=lambda: 0)).once()
    flexmock(module).should_receive('interpret_exit_code').and_return(module.Exit_status.SUCCESS)
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(
        module.execute_command_with_processes(
            full_command,
            processes,
            output_file=module.DO_NOT_CAPTURE,
        )
    )

    assert output_lines == ()


def test_execute_command_with_processes_calls_full_command_with_input_file():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    input_file = flexmock(name='test')
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=input_file,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(
        module.execute_command_with_processes(full_command, processes, input_file=input_file)
    )

    assert output_lines == ()


def test_execute_command_with_processes_calls_full_command_with_shell():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        ' '.join(full_command),
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=True,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(module.execute_command_with_processes(full_command, processes, shell=True))

    assert output_lines == ()


def test_execute_command_with_processes_calls_full_command_with_environment():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env={'a': 'b'},
        cwd=None,
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(
        module.execute_command_with_processes(full_command, processes, environment={'a': 'b'})
    )

    assert output_lines == ()


def test_execute_command_with_processes_calls_full_command_with_working_directory():
    full_command = ['foo', 'bar']
    processes = (flexmock(),)
    flexmock(module).should_receive('log_command')
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd='/working',
        close_fds=False,
    ).and_return(flexmock(stdout=None)).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').and_yield()

    output_lines = tuple(
        module.execute_command_with_processes(
            full_command,
            processes,
            working_directory='/working',
        )
    )

    assert output_lines == ()


def test_execute_command_with_processes_kills_processes_on_error():
    full_command = ['foo', 'bar']
    flexmock(module).should_receive('log_command')
    process = flexmock(stdout=flexmock(read=lambda count: None))
    process.should_receive('poll')
    process.should_receive('kill').once()
    processes = (process,)
    flexmock(module.subprocess).should_receive('Popen').with_args(
        full_command,
        stdin=None,
        stdout=module.subprocess.PIPE,
        stderr=module.subprocess.PIPE,
        shell=False,
        env=None,
        cwd=None,
        close_fds=False,
    ).and_raise(subprocess.CalledProcessError(1, full_command, 'error')).once()
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module).should_receive('log_outputs').never()

    with pytest.raises(subprocess.CalledProcessError):
        tuple(module.execute_command_with_processes(full_command, processes))
