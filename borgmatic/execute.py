import collections
import logging
import os
import select
import subprocess

logger = logging.getLogger(__name__)


ERROR_OUTPUT_MAX_LINE_COUNT = 25
BORG_ERROR_EXIT_CODE = 2


def exit_code_indicates_error(process, exit_code, borg_local_path=None):
    '''
    Return True if the given exit code from running a command corresponds to an error. If a Borg
    local path is given and matches the process' command, then treat exit code 1 as a warning
    instead of an error.
    '''
    if exit_code is None:
        return False

    command = process.args.split(' ') if isinstance(process.args, str) else process.args

    if borg_local_path and command[0] == borg_local_path:
        return bool(exit_code < 0 or exit_code >= BORG_ERROR_EXIT_CODE)

    return bool(exit_code != 0)


def command_for_process(process):
    '''
    Given a process as an instance of subprocess.Popen, return the command string that was used to
    invoke it.
    '''
    return process.args if isinstance(process.args, str) else ' '.join(process.args)


def output_buffer_for_process(process, exclude_stdouts):
    '''
    Given a process as an instance of subprocess.Popen and a sequence of stdouts to exclude, return
    either the process's stdout or stderr. The idea is that if stdout is excluded for a process, we
    still have stderr to log.
    '''
    return process.stderr if process.stdout in exclude_stdouts else process.stdout


def log_outputs(processes, exclude_stdouts, output_log_level, borg_local_path):
    '''
    Given a sequence of subprocess.Popen() instances for multiple processes, log the output for each
    process with the requested log level. Additionally, raise a CalledProcessError if a process
    exits with an error (or a warning for exit code 1, if that process matches the Borg local path).

    If output log level is None, then instead of logging, capture output for each process and return
    it as a dict from the process to its output.

    For simplicity, it's assumed that the output buffer for each process is its stdout. But if any
    stdouts are given to exclude, then for any matching processes, log from their stderr instead.

    Note that stdout for a process can be None if output is intentionally not captured. In which
    case it won't be logged.
    '''
    # Map from output buffer to sequence of last lines.
    buffer_last_lines = collections.defaultdict(list)
    process_for_output_buffer = {
        output_buffer_for_process(process, exclude_stdouts): process
        for process in processes
        if process.stdout or process.stderr
    }
    output_buffers = list(process_for_output_buffer.keys())
    captured_outputs = collections.defaultdict(list)
    still_running = True

    # Log output for each process until they all exit.
    while True:
        if output_buffers:
            (ready_buffers, _, _) = select.select(output_buffers, [], [])

            for ready_buffer in ready_buffers:
                ready_process = process_for_output_buffer.get(ready_buffer)

                # The "ready" process has exited, but it might be a pipe destination with other
                # processes (pipe sources) waiting to be read from. So as a measure to prevent
                # hangs, vent all processes when one exits.
                if ready_process and ready_process.poll() is not None:
                    for other_process in processes:
                        if (
                            other_process.poll() is None
                            and other_process.stdout
                            and other_process.stdout not in output_buffers
                        ):
                            # Add the process's output to output_buffers to ensure it'll get read.
                            output_buffers.append(other_process.stdout)

                while True:
                    line = ready_buffer.readline().rstrip().decode()
                    if not line or not ready_process:
                        break

                    # Keep the last few lines of output in case the process errors, and we need the output for
                    # the exception below.
                    last_lines = buffer_last_lines[ready_buffer]
                    last_lines.append(line)
                    if len(last_lines) > ERROR_OUTPUT_MAX_LINE_COUNT:
                        last_lines.pop(0)

                    if output_log_level is None:
                        captured_outputs[ready_process].append(line)
                    else:
                        logger.log(output_log_level, line)

        if not still_running:
            break

        still_running = False

        for process in processes:
            exit_code = process.poll() if output_buffers else process.wait()

            if exit_code is None:
                still_running = True

            # If any process errors, then raise accordingly.
            if exit_code_indicates_error(process, exit_code, borg_local_path):
                # If an error occurs, include its output in the raised exception so that we don't
                # inadvertently hide error output.
                output_buffer = output_buffer_for_process(process, exclude_stdouts)

                last_lines = buffer_last_lines[output_buffer] if output_buffer else []
                if len(last_lines) == ERROR_OUTPUT_MAX_LINE_COUNT:
                    last_lines.insert(0, '...')

                # Something has gone wrong. So vent each process' output buffer to prevent it from
                # hanging. And then kill the process.
                for other_process in processes:
                    if other_process.poll() is None:
                        other_process.stdout.read(0)
                        other_process.kill()

                raise subprocess.CalledProcessError(
                    exit_code, command_for_process(process), '\n'.join(last_lines)
                )

    if captured_outputs:
        return {
            process: '\n'.join(output_lines) for process, output_lines in captured_outputs.items()
        }


def log_command(full_command, input_file=None, output_file=None):
    '''
    Log the given command (a sequence of command/argument strings), along with its input/output file
    paths.
    '''
    logger.debug(
        ' '.join(full_command)
        + (' < {}'.format(getattr(input_file, 'name', '')) if input_file else '')
        + (' > {}'.format(getattr(output_file, 'name', '')) if output_file else '')
    )


# An sentinel passed as an output file to execute_command() to indicate that the command's output
# should be allowed to flow through to stdout without being captured for logging. Useful for
# commands with interactive prompts or those that mess directly with the console.
DO_NOT_CAPTURE = object()


def execute_command(
    full_command,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    extra_environment=None,
    working_directory=None,
    borg_local_path=None,
    run_to_completion=True,
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its output at the
    given log level. If an open output file object is given, then write stdout to the file and only
    log stderr. If an open input file object is given, then read stdin from the file. If shell is
    True, execute the command within a shell. If an extra environment dict is given, then use it to
    augment the current environment, and pass the result into the command. If a working directory is
    given, use that as the present working directory when running the command. If a Borg local path
    is given, and the command matches it (regardless of arguments), treat exit code 1 as a warning
    instead of an error. If run to completion is False, then return the process for the command
    without executing it to completion.

    Raise subprocesses.CalledProcessError if an error occurs while running the command.
    '''
    log_command(full_command, input_file, output_file)
    environment = {**os.environ, **extra_environment} if extra_environment else None
    do_not_capture = bool(output_file is DO_NOT_CAPTURE)
    command = ' '.join(full_command) if shell else full_command

    process = subprocess.Popen(
        command,
        stdin=input_file,
        stdout=None if do_not_capture else (output_file or subprocess.PIPE),
        stderr=None if do_not_capture else (subprocess.PIPE if output_file else subprocess.STDOUT),
        shell=shell,
        env=environment,
        cwd=working_directory,
    )
    if not run_to_completion:
        return process

    log_outputs(
        (process,), (input_file, output_file), output_log_level, borg_local_path=borg_local_path
    )


def execute_command_and_capture_output(
    full_command, capture_stderr=False, shell=False, extra_environment=None, working_directory=None,
):
    '''
    Execute the given command (a sequence of command/argument strings), capturing and returning its
    output (stdout). If capture stderr is True, then capture and return stderr in addition to
    stdout. If shell is True, execute the command within a shell. If an extra environment dict is
    given, then use it to augment the current environment, and pass the result into the command. If
    a working directory is given, use that as the present working directory when running the command.

    Raise subprocesses.CalledProcessError if an error occurs while running the command.
    '''
    log_command(full_command)
    environment = {**os.environ, **extra_environment} if extra_environment else None
    command = ' '.join(full_command) if shell else full_command

    output = subprocess.check_output(
        command,
        stderr=subprocess.STDOUT if capture_stderr else None,
        shell=shell,
        env=environment,
        cwd=working_directory,
    )

    return output.decode() if output is not None else None


def execute_command_with_processes(
    full_command,
    processes,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    extra_environment=None,
    working_directory=None,
    borg_local_path=None,
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its output at the
    given log level. Simultaneously, continue to poll one or more active processes so that they
    run as well. This is useful, for instance, for processes that are streaming output to a named
    pipe that the given command is consuming from.

    If an open output file object is given, then write stdout to the file and only log stderr. But
    if output log level is None, instead suppress logging and return the captured output for (only)
    the given command. If an open input file object is given, then read stdin from the file. If
    shell is True, execute the command within a shell. If an extra environment dict is given, then
    use it to augment the current environment, and pass the result into the command. If a working
    directory is given, use that as the present working directory when running the command. If a
    Borg local path is given, then for any matching command or process (regardless of arguments),
    treat exit code 1 as a warning instead of an error.

    Raise subprocesses.CalledProcessError if an error occurs while running the command or in the
    upstream process.
    '''
    log_command(full_command, input_file, output_file)
    environment = {**os.environ, **extra_environment} if extra_environment else None
    do_not_capture = bool(output_file is DO_NOT_CAPTURE)
    command = ' '.join(full_command) if shell else full_command

    try:
        command_process = subprocess.Popen(
            command,
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

    captured_outputs = log_outputs(
        tuple(processes) + (command_process,),
        (input_file, output_file),
        output_log_level,
        borg_local_path=borg_local_path,
    )

    if output_log_level is None:
        return captured_outputs.get(command_process)
