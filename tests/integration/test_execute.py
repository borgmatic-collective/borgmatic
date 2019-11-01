import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_execute_and_log_output_logs_each_line_separately():
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'hi').once()
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'there').once()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    module.execute_and_log_output(
        ['echo', 'hi'],
        output_log_level=logging.INFO,
        shell=False,
        environment=None,
        working_directory=None,
        error_on_warnings=False,
    )
    module.execute_and_log_output(
        ['echo', 'there'],
        output_log_level=logging.INFO,
        shell=False,
        environment=None,
        working_directory=None,
        error_on_warnings=False,
    )


def test_execute_and_log_output_includes_error_output_in_exception():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('exit_code_indicates_error').and_return(True)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.execute_and_log_output(
            ['grep'],
            output_log_level=logging.INFO,
            shell=False,
            environment=None,
            working_directory=None,
            error_on_warnings=False,
        )

    assert error.value.returncode == 2
    assert error.value.output


def test_execute_and_log_output_truncates_long_error_output():
    flexmock(module).ERROR_OUTPUT_MAX_LINE_COUNT = 0
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('exit_code_indicates_error').and_return(True)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.execute_and_log_output(
            ['grep'],
            output_log_level=logging.INFO,
            shell=False,
            environment=None,
            working_directory=None,
            error_on_warnings=False,
        )

    assert error.value.returncode == 2
    assert error.value.output.startswith('...')


def test_execute_and_log_output_with_no_output_logs_nothing():
    flexmock(module.logger).should_receive('log').never()
    flexmock(module).should_receive('exit_code_indicates_error').and_return(False)

    module.execute_and_log_output(
        ['true'],
        output_log_level=logging.INFO,
        shell=False,
        environment=None,
        working_directory=None,
        error_on_warnings=False,
    )
