import logging
import os
import subprocess

logger = logging.getLogger(__name__)


ERROR_OUTPUT_MAX_LINE_COUNT = 25
BORG_ERROR_EXIT_CODE = 2


def exit_code_indicates_error(command, exit_code, error_on_warnings=False):
    '''
    Return True if the given exit code from running the command corresponds to an error.
    '''
    # If we're running something other than Borg, treat all non-zero exit codes as errors.
    if 'borg' in command[0] and not error_on_warnings:
        return bool(exit_code >= BORG_ERROR_EXIT_CODE)

    return bool(exit_code != 0)


def log_output(command, process, output_buffer, output_log_level, error_on_warnings):
    '''
    Given a command already executed, its process opened by subprocess.Popen(), and the process'
    relevant output buffer (stderr or stdout), log its output with the requested log level.
    Additionally, raise a CalledProcessException if the process exits with an error (or a warning,
    if error on warnings is True).
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

    if exit_code_indicates_error(command, exit_code, error_on_warnings):
        # If an error occurs, include its output in the raised exception so that we don't
        # inadvertently hide error output.
        if len(last_lines) == ERROR_OUTPUT_MAX_LINE_COUNT:
            last_lines.insert(0, '...')

        raise subprocess.CalledProcessError(exit_code, ' '.join(command), '\n'.join(last_lines))


def execute_command(
    full_command,
    output_log_level=logging.INFO,
    output_file=None,
    input_file=None,
    shell=False,
    extra_environment=None,
    working_directory=None,
    error_on_warnings=False,
):
    '''
    Execute the given command (a sequence of command/argument strings) and log its output at the
    given log level. If output log level is None, instead capture and return the output. If an
    open output file object is given, then write stdout to the file and only log stderr (but only
    if an output log level is set). If an open input file object is given, then read stdin from the
    file. If shell is True, execute the command within a shell. If an extra environment dict is
    given, then use it to augment the current environment, and pass the result into the command. If
    a working directory is given, use that as the present working directory when running the
    command.

    Raise subprocesses.CalledProcessError if an error occurs while running the command.
    '''
    logger.debug(
        ' '.join(full_command)
        + (' < {}'.format(input_file.name) if input_file else '')
        + (' > {}'.format(output_file.name) if output_file else '')
    )
    environment = {**os.environ, **extra_environment} if extra_environment else None

    if output_log_level is None:
        output = subprocess.check_output(
            full_command, shell=shell, env=environment, cwd=working_directory
        )
        return output.decode() if output is not None else None
    else:
        process = subprocess.Popen(
            full_command,
            stdin=input_file,
            stdout=output_file or subprocess.PIPE,
            stderr=subprocess.PIPE if output_file else subprocess.STDOUT,
            shell=shell,
            env=environment,
            cwd=working_directory,
        )
        log_output(
            full_command,
            process,
            process.stderr if output_file else process.stdout,
            output_log_level,
            error_on_warnings,
        )


def execute_command_without_capture(full_command, working_directory=None, error_on_warnings=False):
    '''
    Execute the given command (a sequence of command/argument strings), but don't capture or log its
    output in any way. This is necessary for commands that monkey with the terminal (e.g. progress
    display) or provide interactive prompts.

    If a working directory is given, use that as the present working directory when running the
    command.
    '''
    logger.debug(' '.join(full_command))

    try:
        subprocess.check_call(full_command, cwd=working_directory)
    except subprocess.CalledProcessError as error:
        if exit_code_indicates_error(full_command, error.returncode, error_on_warnings):
            raise
