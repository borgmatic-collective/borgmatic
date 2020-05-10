import collections
import logging
import os
import select
import subprocess

logger = logging.getLogger(__name__)


ERROR_OUTPUT_MAX_LINE_COUNT = 25
BORG_ERROR_EXIT_CODE = 2


def exit_code_indicates_error(exit_code, error_on_warnings=True):
    '''
    Return True if the given exit code from running a command corresponds to an error. If error on
    warnings is False, then treat exit code 1 as a warning instead of an error.
    '''
    if error_on_warnings:
        return bool(exit_code != 0)

    return bool(exit_code >= BORG_ERROR_EXIT_CODE)


def process_command(process):
    '''
    Given a process as an instance of subprocess.Popen, return the command string that was used to
    invoke it.
    '''
    return process.args if isinstance(process.args, str) else ' '.join(process.args)


def log_output(process, output_buffer, output_log_level, error_on_warnings):
    '''
    Given an executed command's process opened by subprocess.Popen(), and the process' relevant
    output buffer (stderr or stdout), log its output with the requested log level. Additionally,
    raise a CalledProcessError if the process exits with an error (or a warning, if error on
    warnings is True).
    '''
    last_lines = []

    while process.poll() is None:
        line = output_buffer.readline().rstrip().decode()
        if not line:
            continue

        # Keep the last few lines of output in case the command errors, and we need the output for
        # the exception below.
        last_lines.append(line)
        if len(last_lines) > ERROR_OUTPUT_MAX_LINE_COUNT:
            last_lines.pop(0)

        logger.log(output_log_level, line)

    remaining_output = output_buffer.read().rstrip().decode()
    if remaining_output:  # pragma: no cover
        logger.log(output_log_level, remaining_output)

    exit_code = process.poll()

    if exit_code_indicates_error(exit_code, error_on_warnings):
        # If an error occurs, include its output in the raised exception so that we don't
        # inadvertently hide error output.
        if len(last_lines) == ERROR_OUTPUT_MAX_LINE_COUNT:
            last_lines.insert(0, '...')

        raise subprocess.CalledProcessError(
            exit_code, process_command(process), '\n'.join(last_lines)
        )


def output_buffer_for_process(process, exclude_stdouts):
    '''
    Given an instance of subprocess.Popen and a sequence of stdouts to exclude, return either the
    process's stdout or stderr. The idea is that if stdout is excluded for a process, we still have
    stderr to log.
    '''
    return process.stderr if process.stdout in exclude_stdouts else process.stdout


def log_many_outputs(processes, exclude_stdouts, output_log_level, error_on_warnings):
    '''
    Given a sequence of subprocess.Popen() instances for multiple processes, log the output for each
    process with the requested log level. Additionally, raise a CalledProcessError if a process
    exits with an error (or a warning, if error on warnings is True).

    For simplicity, it's assumed that the output buffer for each process is its stdout. But if any
    stdouts are given to exclude, then for any matching processes, log from their stderr instead.
    '''
    # Map from output buffer to sequence of last lines.
    buffer_last_lines = collections.defaultdict(list)
    output_buffers = [
        output_buffer_for_process(process, exclude_stdouts)
        for process in processes
        if process.stdout or process.stderr
    ]

    while True:
        (ready_buffers, _, _) = select.select(output_buffers, [], [])

        for ready_buffer in ready_buffers:
            line = ready_buffer.readline().rstrip().decode()
            if not line:
                continue

            # Keep the last few lines of output in case the process errors, and we need the output for
            # the exception below.
            last_lines = buffer_last_lines[ready_buffer]
            last_lines.append(line)
            if len(last_lines) > ERROR_OUTPUT_MAX_LINE_COUNT:
                last_lines.pop(0)

            logger.log(output_log_level, line)

        if all(process.poll() is not None for process in processes):
            break

    for process in processes:
        output_buffer = output_buffer_for_process(process, exclude_stdouts)

        if not output_buffer:
            continue

        remaining_output = output_buffer.read().rstrip().decode()

        if remaining_output:  # pragma: no cover
            logger.log(output_log_level, remaining_output)

    for process in processes:
        exit_code = process.poll()

        if exit_code_indicates_error(exit_code, error_on_warnings):
            # If an error occurs, include its output in the raised exception so that we don't
            # inadvertently hide error output.
            output_buffer = output_buffer_for_process(process, exclude_stdouts)

            last_lines = buffer_last_lines[output_buffer] if output_buffer else []
            if len(last_lines) == ERROR_OUTPUT_MAX_LINE_COUNT:
                last_lines.insert(0, '...')

            raise subprocess.CalledProcessError(
                exit_code, process_command(process), '\n'.join(last_lines)
            )


def log_command(full_command, input_file, output_file):
    '''
    Log the given command (a sequence of command/argument strings), along with its input/output file
    paths.
    '''
    logger.debug(
        ' '.join(full_command)
        + (' < {}'.format(getattr(input_file, 'name', '')) if input_file else '')
        + (' > {}'.format(getattr(output_file, 'name', '')) if output_file else '')
    )


DO_NOT_CAPTURE = object()


def execute_command(
    full_command,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    extra_environment=None,
    working_directory=None,
    error_on_warnings=True,
    run_to_completion=True,
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its output at the
    given log level. If output log level is None, instead capture and return the output. (Implies
    run_to_completion.) If an open output file object is given, then write stdout to the file and
    only log stderr (but only if an output log level is set). If an open input file object is given,
    then read stdin from the file. If shell is True, execute the command within a shell. If an extra
    environment dict is given, then use it to augment the current environment, and pass the result
    into the command. If a working directory is given, use that as the present working directory
    when running the command. If error on warnings is False, then treat exit code 1 as a warning
    instead of an error. If run to completion is False, then return the process for the command
    without executing it to completion.

    Raise subprocesses.CalledProcessError if an error occurs while running the command.
    '''
    log_command(full_command, input_file, output_file)
    environment = {**os.environ, **extra_environment} if extra_environment else None
    do_not_capture = bool(output_file is DO_NOT_CAPTURE)

    if output_log_level is None:
        output = subprocess.check_output(
            full_command, shell=shell, env=environment, cwd=working_directory
        )
        return output.decode() if output is not None else None

    process = subprocess.Popen(
        ' '.join(full_command) if shell else full_command,
        stdin=input_file,
        stdout=None if do_not_capture else (output_file or subprocess.PIPE),
        stderr=None if do_not_capture else (subprocess.PIPE if output_file else subprocess.STDOUT),
        shell=shell,
        env=environment,
        cwd=working_directory,
    )
    if not run_to_completion:
        return process

    if do_not_capture:
        exit_code = process.wait()

        if exit_code_indicates_error(exit_code, error_on_warnings):
            raise subprocess.CalledProcessError(exit_code, process_command(process))

        return None

    log_output(
        process,
        process.stderr if output_file else process.stdout,
        output_log_level,
        error_on_warnings,
    )


def execute_command_with_processes(
    full_command,
    processes,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    extra_environment=None,
    working_directory=None,
    error_on_warnings=True,
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its output at the
    given log level. Simultaneously, continue to poll one or more active processes so that they
    run as well. This is useful, for instance, for processes that are streaming output to a named
    pipe that the given command is consuming from.

    If an open output file object is given, then write stdout to the file and only log stderr (but
    only if an output log level is set). If an open input file object is given, then read stdin from
    the file.  If shell is True, execute the command within a shell. If an extra environment dict is
    given, then use it to augment the current environment, and pass the result into the command. If
    a working directory is given, use that as the present working directory when running the
    command.  If error on warnings is False, then treat exit code 1 as a warning instead of an
    error.

    Raise subprocesses.CalledProcessError if an error occurs while running the command or in the
    upstream process.
    '''
    log_command(full_command, input_file, output_file)
    environment = {**os.environ, **extra_environment} if extra_environment else None
    do_not_capture = bool(output_file is DO_NOT_CAPTURE)

    try:
        command_process = subprocess.Popen(
            full_command,
            stdin=input_file,
            stdout=None if do_not_capture else (output_file or subprocess.PIPE),
            stderr=None
            if do_not_capture
            else (subprocess.PIPE if output_file else subprocess.STDOUT),
            shell=shell,
            env=environment,
            cwd=working_directory,
        )
    except (subprocess.CalledProcessError, OSError):
        # Something has gone wrong. So vent each process' output buffer to prevent it from hanging.
        # And then kill the process.
        for process in processes:
            if process.poll() is None:
                process.stdout.read(0)
                process.kill()
        raise

    log_many_outputs(
        tuple(processes) + (command_process,),
        (input_file, output_file),
        output_log_level,
        error_on_warnings,
    )
