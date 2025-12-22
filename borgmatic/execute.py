import collections
import enum
import logging
import select
import subprocess
import textwrap

import borgmatic.logger

logger = logging.getLogger(__name__)


ERROR_OUTPUT_MAX_LINE_COUNT = 25
BORG_ERROR_EXIT_CODE_START = 2
BORG_ERROR_EXIT_CODE_END = 99


class Exit_status(enum.Enum):
    STILL_RUNNING = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4


def interpret_exit_code(command, exit_code, borg_local_path=None, borg_exit_codes=None):
    '''
    Return an Exit_status value (e.g. SUCCESS, ERROR, or WARNING) based on interpreting the given
    exit code. If a Borg local path is given and matches the process' command, then interpret the
    exit code based on Borg's documented exit code semantics. And if Borg exit codes are given as a
    sequence of exit code configuration dicts, then take those configured preferences into account.
    '''
    if exit_code is None:
        return Exit_status.STILL_RUNNING

    if exit_code == 0:
        return Exit_status.SUCCESS

    if borg_local_path and command[0] == borg_local_path:
        # First try looking for the exit code in the borg_exit_codes configuration.
        for entry in borg_exit_codes or ():
            if entry.get('code') == exit_code:
                treat_as = entry.get('treat_as')

                if treat_as == 'error':
                    logger.error(
                        f'Treating exit code {exit_code} as an error, as per configuration',
                    )
                    return Exit_status.ERROR

                if treat_as == 'warning':
                    logger.warning(
                        f'Treating exit code {exit_code} as a warning, as per configuration',
                    )
                    return Exit_status.WARNING

        # If the exit code doesn't have explicit configuration, then fall back to the default Borg
        # behavior.
        return (
            Exit_status.ERROR
            if (
                exit_code < 0
                or (
                    exit_code >= BORG_ERROR_EXIT_CODE_START
                    and exit_code <= BORG_ERROR_EXIT_CODE_END
                )
            )
            else Exit_status.WARNING
        )

    return Exit_status.ERROR


def command_for_process(process):
    '''
    Given a process as an instance of subprocess.Popen, return the command string that was used to
    invoke it.
    '''
    return process.args if isinstance(process.args, str) else ' '.join(process.args)


def output_buffers_for_process(process, exclude_stdouts):
    '''
    Given a process as an instance of subprocess.Popen and a sequence of stdouts to exclude, return
    the process stdout and stderr as a tuple—but exclude the stdout if it's in the given stdouts to
    exclude.
    '''
    return tuple(
        buffer for buffer in (process.stdout, process.stderr) if buffer not in exclude_stdouts
    )


def determine_log_level(output_log_level, came_from_stderr, borg_local_path, command, line):
    '''
    Given the requested output log level, whether the this log line came from stderr, the Borg local
    path, the command as a sequence, and the line to be logged, return the log level that should be
    used.

    Borg happens to log everything to stderr (except JSON output), so if this is a Borg command, use
    the requested log level regardless of whether this is for stdout or stderr. (Otherwise, all Borg
    logs would show up at ERROR level even if there's no error!)

    But for other commands, elevate stderr logs to ERROR while using the requested log level for
    stdout. The one exception is if the log came from stderr and the string "warning" appears at the
    start of the log line. In that case, just elevate the log level to a WARN.
    '''
    if borg_local_path and command[0] == borg_local_path:
        return output_log_level

    if came_from_stderr:
        return logging.WARN if line.lower().startswith('warning:') else logging.ERROR

    return output_log_level


def append_last_lines(last_lines, captured_output, line, log_level):
    '''
    Given a rolling list of last lines, a list of captured output, a line to append, and an output
    log level, append the line to the last lines and (if necessary) the captured output. Then log
    the line at the requested log level.
    '''
    last_lines.append(line)

    if len(last_lines) > ERROR_OUTPUT_MAX_LINE_COUNT:
        last_lines.pop(0)

    if log_level is None:
        captured_output.append(line)
    else:
        logger.log(log_level, line)


def log_outputs(processes, exclude_stdouts, output_log_level, borg_local_path, borg_exit_codes):  # noqa: PLR0912
    '''
    Given a sequence of subprocess.Popen() instances for multiple processes, log the outputs (stderr
    and stdout). Use the requested output log level for stdout, but always log stderr to the ERROR
    log level. Additionally, raise a CalledProcessError if a process exits with an error (or a
    warning for exit code 1, if that process does not match the Borg local path).

    If output log level is None, then instead of logging, capture output for each process and return
    it as a dict from the process to its output. Use the given Borg local path and exit code
    configuration to decide what's an error and what's a warning.

    If any stdouts are given to exclude, then for any matching processes, ignore those buffers. Also
    note that stdout for a process can be None if output is intentionally not captured, in which
    case it won't be logged.
    '''
    # Map from output buffer to sequence of last lines.
    buffer_last_lines = collections.defaultdict(list)
    process_for_output_buffer = {
        buffer: process
        for process in processes
        if process.stdout or process.stderr
        for buffer in output_buffers_for_process(process, exclude_stdouts)
    }
    output_buffers = list(process_for_output_buffer.keys())
    captured_outputs = collections.defaultdict(list)
    still_running = True

    # Log output for each process until they all exit.
    while True:  # noqa: PLR1702
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

                    command = (
                        ready_process.args.split(' ')
                        if isinstance(ready_process.args, str)
                        else ready_process.args
                    )

                    # Keep the last few lines of output in case the process errors, and we need the
                    # output for the exception below.
                    append_last_lines(
                        buffer_last_lines[ready_buffer],
                        captured_outputs[ready_process],
                        line,
                        determine_log_level(
                            output_log_level,
                            (ready_buffer == ready_process.stderr),
                            borg_local_path,
                            command,
                            line,
                        ),
                    )

        if not still_running:
            break

        still_running = False

        for process in processes:
            exit_code = process.poll() if output_buffers else process.wait()

            if exit_code is None:
                still_running = True
                command = process.args.split(' ') if isinstance(process.args, str) else process.args
                continue

            command = process.args.split(' ') if isinstance(process.args, str) else process.args
            exit_status = interpret_exit_code(command, exit_code, borg_local_path, borg_exit_codes)

            if exit_status in {Exit_status.ERROR, Exit_status.WARNING}:
                # execute_command_and_capture_output If an error occurs, include its output in the raised exception so that we don't
                # inadvertently hide error output.
                for output_buffer in output_buffers_for_process(process, exclude_stdouts):
                    last_lines = buffer_last_lines[output_buffer] if output_buffer else []

                    # Collect any straggling output lines that came in since we last gathered output.
                    while output_buffer:  # pragma: no cover
                        line = output_buffer.readline().rstrip().decode()
                        if not line:
                            break

                        append_last_lines(
                            last_lines,
                            captured_outputs[process],
                            line,
                            determine_log_level(
                                output_log_level,
                                (output_buffer == process.stderr),
                                borg_local_path,
                                command,
                                line,
                            ),
                        )

                if len(last_lines) == ERROR_OUTPUT_MAX_LINE_COUNT:
                    last_lines.insert(0, '...')

                # Something has gone wrong. So vent each process' output buffer to prevent it from
                # hanging. And then kill the process.
                for other_process in processes:
                    if other_process.poll() is None:
                        other_process.stdout.read(0)
                        other_process.kill()

                if exit_status == Exit_status.ERROR:
                    raise subprocess.CalledProcessError(
                        exit_code,
                        command_for_process(process),
                        '\n'.join(last_lines),
                    )

                still_running = False
                break

    if captured_outputs:
        return {
            process: '\n'.join(output_lines) for process, output_lines in captured_outputs.items()
        }

    return None


SECRET_COMMAND_FLAG_NAMES = {'--password'}


def mask_command_secrets(full_command):
    '''
    Given a command as a sequence, mask secret values for flags like "--password" in preparation for
    logging.
    '''
    masked_command = []
    previous_piece = None

    for piece in full_command:
        masked_command.append('***' if previous_piece in SECRET_COMMAND_FLAG_NAMES else piece)
        previous_piece = piece

    return tuple(masked_command)


MAX_LOGGED_COMMAND_LENGTH = 1000


PREFIXES_OF_ENVIRONMENT_VARIABLES_TO_LOG = ('BORG_', 'PG', 'MARIADB_', 'MYSQL_')


def log_command(full_command, input_file=None, output_file=None, environment=None):
    '''
    Log the given command (a sequence of command/argument strings), along with its input/output file
    paths and extra environment variables (with omitted values in case they contain passwords).
    '''
    logger.debug(
        textwrap.shorten(
            ' '.join(
                tuple(
                    f'{key}=***'
                    for key in (environment or {})
                    if any(
                        key.startswith(prefix)
                        for prefix in PREFIXES_OF_ENVIRONMENT_VARIABLES_TO_LOG
                    )
                )
                + mask_command_secrets(full_command),
            ),
            width=MAX_LOGGED_COMMAND_LENGTH,
            placeholder=' ...',
        )
        + (f" < {getattr(input_file, 'name', input_file)}" if input_file else '')
        + (f" > {getattr(output_file, 'name', output_file)}" if output_file else ''),
    )


# A sentinel passed as an output file to execute_command() to indicate that the command's output
# should be allowed to flow through to stdout without being captured for logging. Useful for
# commands with interactive prompts or those that mess directly with the console.
DO_NOT_CAPTURE = object()


def execute_command(
    full_command,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    environment=None,
    working_directory=None,
    borg_local_path=None,
    borg_exit_codes=None,
    run_to_completion=True,
    close_fds=False,  # Necessary for passing credentials via anonymous pipe.
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its stdout output at
    the given log level. If an open output file object is given, then write stdout to the file and
    only log stderr. If an open input file object is given, then read stdin from the file. If shell
    is True, execute the command within a shell. If an environment variables dict is given, then
    pass it into the command. If a working directory is given, use that as the present working
    directory when running the command. If a Borg local path is given, and the command matches it
    (regardless of arguments), treat exit code 1 as a warning instead of an error. But if Borg exit
    codes are given as a sequence of exit code configuration dicts, then use that configuration to
    decide what's an error and what's a warning. If run to completion is False, then return the
    process for the command without executing it to completion.

    Raise subprocesses.CalledProcessError if an error occurs while running the command.
    '''
    log_command(full_command, input_file, output_file, environment)
    do_not_capture = bool(output_file is DO_NOT_CAPTURE)
    command = ' '.join(full_command) if shell else full_command

    process = subprocess.Popen(  # noqa: S603
        command,
        stdin=input_file,
        stdout=None if do_not_capture else (output_file or subprocess.PIPE),
        stderr=None if do_not_capture else subprocess.PIPE,
        shell=shell,
        env=environment,
        cwd=working_directory,
        close_fds=close_fds,
    )
    if not run_to_completion:
        return process

    with borgmatic.logger.Log_prefix(None):  # Log command output without any prefix.
        log_outputs(
            (process,),
            (input_file, output_file),
            output_log_level,
            borg_local_path,
            borg_exit_codes,
        )

    return None


def execute_command_and_capture_output(
    full_command,
    input_file=None,
    capture_stderr=False,
    shell=False,
    environment=None,
    working_directory=None,
    borg_local_path=None,
    borg_exit_codes=None,
    close_fds=False,  # Necessary for passing credentials via anonymous pipe.
):
    '''
    Execute the given command (a sequence of command/argument strings), capturing and returning its
    output (stdout). If an input file descriptor is given, then pipe it to the command's stdin. If
    capture stderr is True, then capture and return stderr in addition to stdout. If shell is True,
    execute the command within a shell. If an environment variables dict is given, then pass it into
    the command. If a working directory is given, use that as the present working directory when
    running the command. If a Borg local path is given, and the command matches it (regardless of
    arguments), treat exit code 1 as a warning instead of an error. But if Borg exit codes are given
    as a sequence of exit code configuration dicts, then use that configuration to decide what's an
    error and what's a warning.

    Raise subprocesses.CalledProcessError if an error occurs while running the command.
    '''
    log_command(full_command, input_file, environment=environment)
    command = ' '.join(full_command) if shell else full_command

    try:
        process = subprocess.Popen(  # noqa: S603
            command,
            stdin=input_file,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            env=environment,
            cwd=working_directory,
            close_fds=close_fds,
        )
    except subprocess.CalledProcessError as error:
        if (
            interpret_exit_code(command, error.returncode, borg_local_path, borg_exit_codes)
            == Exit_status.ERROR
        ):
            raise

        return error.output.decode() if error.output is not None else None

    with borgmatic.logger.Log_prefix(None):  # Log command output without any prefix.
        captured_outputs = log_outputs(
            (process,),
            (input_file,),
            None,
            borg_local_path,
            borg_exit_codes,
        )

    return captured_outputs.get(process)


def execute_command_with_processes(
    full_command,
    processes,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    environment=None,
    working_directory=None,
    borg_local_path=None,
    borg_exit_codes=None,
    close_fds=False,  # Necessary for passing credentials via anonymous pipe.
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its stdout output at
    the given log level. Simultaneously, continue to poll one or more active processes so that they
    run as well. This is useful, for instance, for processes that are streaming output to a named
    pipe that the given command is consuming from.

    If an open output file object is given, then write stdout to the file and only log stderr. But
    if output log level is None, instead suppress logging and return the captured output for (only)
    the given command. If an open input file object is given, then read stdin from the file. If
    shell is True, execute the command within a shell. If an environment variables dict is given,
    then pass it into the command. If a working directory is given, use that as the present working
    directory when running the command. If a Borg local path is given, then for any matching command
    or process (regardless of arguments), treat exit code 1 as a warning instead of an error. But if
    Borg exit codes are given as a sequence of exit code configuration dicts, then use that
    configuration to decide what's an error and what's a warning.

    Raise subprocesses.CalledProcessError if an error occurs while running the command or in the
    upstream process.
    '''
    log_command(full_command, input_file, output_file, environment)
    do_not_capture = bool(output_file is DO_NOT_CAPTURE)
    command = ' '.join(full_command) if shell else full_command

    try:
        command_process = subprocess.Popen(  # noqa: S603
            command,
            stdin=input_file,
            stdout=None if do_not_capture else (output_file or subprocess.PIPE),
            stderr=None if do_not_capture else subprocess.PIPE,
            shell=shell,
            env=environment,
            cwd=working_directory,
            close_fds=close_fds,
        )
    except (subprocess.CalledProcessError, OSError):
        # Something has gone wrong. So vent each process' output buffer to prevent it from hanging.
        # And then kill the process.
        for process in processes:
            if process.poll() is None:
                process.stdout.read(0)
                process.kill()

        raise

    with borgmatic.logger.Log_prefix(None):  # Log command output without any prefix.
        captured_outputs = log_outputs(
            (*processes, command_process),
            (input_file, output_file),
            output_log_level,
            borg_local_path,
            borg_exit_codes,
        )

    if output_log_level is None:
        return captured_outputs.get(command_process)

    return None
