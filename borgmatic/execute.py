import collections
import contextlib
import enum
import json
import logging
import os
import select
import subprocess
import textwrap
import time

import borgmatic.logger

logger = logging.getLogger(__name__)


ERROR_OUTPUT_MAX_LINE_COUNT = 25
BORG_ERROR_EXIT_CODE_START = 2
BORG_ERROR_EXIT_CODE_END = 99

# See https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#message-ids
BORG_WARNING_EXIT_CODES_TREATED_AS_ERRORS = {101, 102, 104, 105, 106, 107}


class Exit_status(enum.Enum):
    STILL_RUNNING = 1
    SUCCESS = 2
    WARNING = 3
    ERROR = 4


def interpret_exit_code(command, exit_code, borg_local_path=None, borg_exit_codes=None):  # noqa: PLR0911
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

    parsed_command = command.split(' ', 1) if isinstance(command, str) else command

    if borg_local_path and parsed_command[0] == borg_local_path:
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

        # If the exit code doesn't have explicit configuration, then fall back to the default
        # behavior of treating Borg errors as errors and some Borg warnings as errors.
        if exit_code in BORG_WARNING_EXIT_CODES_TREATED_AS_ERRORS:
            logger.error(
                f'Treating exit code {exit_code} as an error, as per borgmatic defaults',
            )

            return Exit_status.ERROR

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


def borg_json_log_line_to_record(line, log_level):
    '''
    Given a single Borg "--log-json"-style log line and a log level, return the line converted to a
    logging.LogRecord instance. Return None if the line can't be parsed as JSON.
    '''
    with contextlib.suppress(json.JSONDecodeError, TypeError, KeyError, AttributeError):
        log_data = json.loads(line)
        log_type = log_data.get('type')

        if log_type == 'log_message':
            return logging.makeLogRecord(
                dict(
                    levelno=logging._nameToLevel.get(log_data.get('levelname')),
                    created=log_data.get('time'),
                    msg=log_data.get('message'),
                    levelname=log_data.get('levelname'),
                    name=log_data.get('name'),
                )
            )

        if log_type == 'file_status':
            return logging.makeLogRecord(
                dict(
                    levelno=log_level,
                    created=time.time(),
                    msg=f'{log_data.get("status")} {log_data.get("path")}',
                    levelname=logging.getLevelName(log_level),
                    name='borg.file_status',
                )
            )

    return None


def log_line_to_record(line, log_level):
    '''
    Given a log data dict for a single Borg log entry and a log level, return it converted to a
    logging.LogRecord instance.
    '''
    return logging.makeLogRecord(
        dict(
            msg=line,
            levelno=log_level,
            levelname=logging.getLevelName(log_level),
        )
    )


def parse_log_line(line, log_level, elevate_stderr, borg_local_path, command):
    '''
    Given a raw output line from an external program, whether this line came from stderr and should
    be elevated to error/warning, the Borg local path, and the command as a sequence, return a
    logging.LogRecord instance containing its parsed data.

    If the command being run is Borg, and the log line is JSON-formatted log data, then grab the log
    level from it and log the parsed JSON to be consumed later by a Python logging.Formatter.

    But for non-Borg commands, elevate stderr-sourced logs to ERROR. The one exception is if the log
    came from stderr and the string "warning:" appears at the start of the log line. In that case,
    just elevate the log level to a WARN.
    '''
    parsed_command = command.split(' ', 1) if isinstance(command, str) else command

    if borg_local_path and parsed_command[0] == borg_local_path:
        log_record = borg_json_log_line_to_record(line, log_level)

        if log_record:
            return log_record

    if elevate_stderr:
        return log_line_to_record(
            line, logging.WARNING if line.lower().startswith('warning:') else logging.ERROR
        )

    return log_line_to_record(line, log_level)


def handle_log_record(log_record, last_lines=None):
    '''
    Given a log record to be logged and a rolling list of last lines, append the record's message to
    the last lines (if given). Then (if the log level is not None), log the record.

    Return the log record.
    '''
    log_message = log_record.getMessage()

    if last_lines is not None:
        last_lines.append(log_message)

        if len(last_lines) > ERROR_OUTPUT_MAX_LINE_COUNT:
            last_lines.pop(0)

    if log_record.levelno is not None:
        logger.handle(log_record)

    return log_record


READ_CHUNK_SIZE = 4096


def read_lines(buffer, process, line_separator='\n'):
    '''
    Given a Python buffer (like stdout) ready for reading, its process, and a line separator,
    repeatedly yield a tuple of (decoded) lines from the buffer until the process has exited.

    It is assumed that this function's generator is used in conjunction with an external select()
    call to know when to read more lines. Otherwise, the generator will busywait if it's called in a
    tight loop.
    '''
    data = ''

    while True:
        chunk = os.read(buffer.fileno(), READ_CHUNK_SIZE).decode()

        if not chunk:  # EOF
            # The process is still running, so we keep running too.
            if process.poll() is None:
                continue

            break

        data += chunk
        lines = []

        # Split the data into lines, holding back anything leftover that might
        # be a partial line.
        while True:
            separator_position = data.find(line_separator)

            if separator_position == -1:
                break

            lines.append(data[:separator_position].rstrip())
            data = data[separator_position + 1 :]

        yield tuple(lines)

    # Yield any leftover data from the end of the buffer.
    if data:
        yield (data.rstrip(),)


Buffer_reader = collections.namedtuple(
    'Buffer_reader',
    ('lines', 'process'),
)


Process_metadata = collections.namedtuple(
    'Process_metadata',
    ('last_lines', 'capture'),
)


def log_buffer_lines(
    buffer_readers, process_metadatas, output_log_level, borg_local_path, capture_stderr=False
):
    '''
    Given a dict from buffer object to Buffer_reader, a dict from subprocess.Popen() instance to
    Process_metadata instance, a requested output log level for stdout, Borg's local path, and
    whether to capture stderr, read and log any ready output lines from the buffers.  Additionally,
    if the log level is None for any log record, then yield those log messages for capture.

    This function just does one "turn of the crank" of logging buffer output. It is intended to be
    called repeatedly to continue to process buffers.
    '''
    if not buffer_readers:
        return

    (ready_buffers, _, _) = select.select(buffer_readers.keys(), [], [])

    for ready_buffer in ready_buffers:
        reader = buffer_readers[ready_buffer]

        # The "ready" process has exited, but it might be a pipe destination with other
        # processes (pipe sources) waiting to be read from. So as a measure to prevent
        # hangs, vent all processes when one exits.
        if reader.process and reader.process.poll() is not None:
            for other_process in process_metadatas:
                if (
                    other_process.poll() is None
                    and other_process.stdout
                    and other_process.stdout not in buffer_readers
                ):
                    # Add the process's output to buffer_readers to ensure it'll get read.
                    buffer_readers[other_process.stdout] = Buffer_reader(
                        read_lines(other_process.stdout, other_process), other_process
                    )

        try:
            lines = next(reader.lines)
        except StopIteration:
            continue

        for line in lines:
            if not line or not reader.process:
                continue

            # Keep the last few lines of output in case the process errors and we need the
            # output for the exception below.
            log_record = handle_log_record(
                parse_log_line(
                    line=line,
                    log_level=output_log_level,
                    elevate_stderr=(ready_buffer == reader.process.stderr and not capture_stderr),
                    borg_local_path=borg_local_path,
                    command=reader.process.args,
                ),
                last_lines=process_metadatas[reader.process].last_lines,
            )

            if log_record.levelno is None and process_metadatas[reader.process].capture:
                yield log_record.getMessage()


def raise_for_process_errors(buffer_readers, process_metadatas, borg_local_path, borg_exit_codes):
    '''
    Given a dict from buffer object to Buffer_reader, a dict from subprocess.Popen() instance to
    Process_metadata instance, Borg's local path, a sequence of exit code configuration dicts, check
    the given processes for error or warning exit codes. If found, vent or kill any running
    processes. In the case of an error exit code, raise. In the case of warning, return
    Exit_status.WARNING. Otherwise, return None.
    '''
    result_status = None

    for process in process_metadatas:
        exit_code = process.poll() if buffer_readers else process.wait()

        if exit_code is None:
            continue

        exit_status = interpret_exit_code(process.args, exit_code, borg_local_path, borg_exit_codes)

        if exit_status not in {Exit_status.ERROR, Exit_status.WARNING}:
            continue

        # Something has gone wrong. So vent each process' output buffer to prevent it from
        # hanging. And then kill the process.
        for other_process in process_metadatas:
            if other_process.poll() is None:
                other_process.stdout.read(0)
                other_process.kill()

        if exit_status == Exit_status.WARNING:
            result_status = Exit_status.WARNING
            continue

        last_lines = process_metadatas[process].last_lines

        # If an error occurs, include its output in the raised exception so that we don't
        # inadvertently hide error output.
        if len(last_lines) >= ERROR_OUTPUT_MAX_LINE_COUNT:
            last_lines.insert(0, '...')

        raise subprocess.CalledProcessError(
            exit_code,
            command_for_process(process),
            '\n'.join(last_lines),
        )

    return result_status


def log_remaining_buffer_lines(
    buffer_readers, process_metadatas, output_log_level, borg_local_path, capture_stderr=False
):
    '''
    Given a dict from buffer object to Buffer_reader, a dict from subprocess.Popen() instance to
    Process_metadata instance, a requested output log level for stdout, Borg's local path, and
    whether to capture stderr, drain and log any remaining output lines from the buffers until
    they're empty. Additionally, if the log level is None for any log record, then yield those log
    messages for capture.
    '''
    for output_buffer, reader in buffer_readers.items():
        if not reader.process:
            continue

        for lines in reader.lines:
            for line in lines:
                log_record = handle_log_record(
                    parse_log_line(
                        line=line.rstrip(),
                        log_level=output_log_level,
                        elevate_stderr=(
                            output_buffer == reader.process.stderr and not capture_stderr
                        ),
                        borg_local_path=borg_local_path,
                        command=reader.process.args,
                    ),
                )

                if log_record.levelno is None and process_metadatas[reader.process].capture:
                    yield log_record.getMessage()


def log_outputs(
    processes,
    exclude_stdouts,
    output_log_level,
    borg_local_path,
    borg_exit_codes,
    capture_stderr=False,
):
    '''
    Given a sequence of subprocess.Popen() instances for multiple processes, log the outputs (stderr
    and stdout). Use the requested output log level for stdout, but always log stderr to the ERROR
    log level. Additionally, raise a CalledProcessError if a process exits with an error (or a
    warning for exit code 1, if that process does not match the Borg local path).

    If the output log level is None, then instead of logging, capture the output for the last
    process given and yield it one line at a time. This includes stderr if capture stderr is set.
    But if the output log level is not None, don't yield anything.

    This yielding means that this function is a generator, and must be consumed in order to execute.

    Use the given Borg local path and exit code configuration to decide what's an error and what's a
    warning. If any stdouts are given to exclude, then for any matching processes, ignore those
    buffers. Also note that stdout for a process can be None if output is intentionally not
    captured, in which case it won't be logged.
    '''
    # Map from output buffer to Process_metadata instance. By convention, the last process is the
    # process to capture.
    process_metadatas = {
        process: Process_metadata(last_lines=[], capture=bool(process == processes[-1]))
        for process in processes
    }

    # Map from buffer to Buffer_reader instance.
    buffer_readers = {
        buffer: Buffer_reader(read_lines(buffer, process), process)
        for process in processes
        if process.stdout or process.stderr
        for buffer in output_buffers_for_process(process, exclude_stdouts)
    }

    # Log output lines for each process until they all exit.
    while True:
        yield from log_buffer_lines(
            buffer_readers, process_metadatas, output_log_level, borg_local_path, capture_stderr
        )

        if (
            raise_for_process_errors(
                buffer_readers, process_metadatas, borg_local_path, borg_exit_codes
            )
            == Exit_status.WARNING
        ):
            break

        if all(process.poll() is not None for process in processes):
            break

    # Now that all processes have exited, drain and consume any last output.
    yield from log_remaining_buffer_lines(
        buffer_readers, process_metadatas, output_log_level, borg_local_path, capture_stderr
    )


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
        tuple(
            log_outputs(
                (process,),
                (input_file, output_file),
                output_log_level,
                borg_local_path,
                borg_exit_codes,
            )
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
    output (stdout) as a generator that yields one line at a time. The generator must be consumed in
    order for the called command to execute.

    If an input file descriptor is given, then pipe it to the command's stdin. If capture stderr is
    True, then capture stderr in addition to stdout. If shell is True, execute the command within a
    shell. If an environment variables dict is given, then pass it into the command. If a working
    directory is given, use that as the present working directory when running the command. If a
    Borg local path is given, and the command matches it (regardless of arguments), treat exit code
    1 as a warning instead of an error. But if Borg exit codes are given as a sequence of exit code
    configuration dicts, then use that configuration to decide what's an error and what's a warning.

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

        if error.output is not None:
            yield from iter(error.output.decode().splitlines())

        return

    with borgmatic.logger.Log_prefix(None):  # Log command output without any prefix.
        captured_lines = log_outputs(
            (process,),
            (input_file,),
            None,
            borg_local_path,
            borg_exit_codes,
            capture_stderr=capture_stderr,
        )

    yield from captured_lines


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
    the given command as a generator that yields one line at a time. The generator must be consumed
    in order for the called command to execute—regardless of the output log level.

    If an open input file object is given, then read stdin from the file. If shell is True, execute
    the command within a shell. If an environment variables dict is given, then pass it into the
    command. If a working directory is given, use that as the present working directory when running
    the command. If a Borg local path is given, then for any matching command or process (regardless
    of arguments), treat exit code 1 as a warning instead of an error. But if Borg exit codes are
    given as a sequence of exit code configuration dicts, then use that configuration to decide
    what's an error and what's a warning.

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
        captured_lines = log_outputs(
            (*processes, command_process),
            (input_file, output_file),
            output_log_level,
            borg_local_path,
            borg_exit_codes,
        )

    yield from captured_lines
