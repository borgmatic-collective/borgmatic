import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_borg_command_identifies_borg_command():
    assert module.borg_command(['/usr/bin/borg1', 'info'])


def test_borg_command_does_not_identify_other_command():
    assert not module.borg_command(['grep', 'stuff'])


def test_execute_and_log_output_logs_each_line_separately():
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'hi').once()
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'there').once()
    flexmock(module).should_receive('borg_command').and_return(False)

    module.execute_and_log_output(
        ['echo', 'hi'], output_log_level=logging.INFO, shell=False, environment=None
    )
    module.execute_and_log_output(
        ['echo', 'there'], output_log_level=logging.INFO, shell=False, environment=None
    )


def test_execute_and_log_output_with_borg_warning_does_not_raise():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('borg_command').and_return(True)

    module.execute_and_log_output(
        ['false'], output_log_level=logging.INFO, shell=False, environment=None
    )


def test_execute_and_log_output_includes_borg_error_output_in_exception():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('borg_command').and_return(True)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.execute_and_log_output(
            ['grep'], output_log_level=logging.INFO, shell=False, environment=None
        )

    assert error.value.returncode == 2
    assert error.value.output


def test_execute_and_log_output_with_non_borg_error_raises():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('borg_command').and_return(False)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.execute_and_log_output(
            ['false'], output_log_level=logging.INFO, shell=False, environment=None
        )

    assert error.value.returncode == 1


def test_execute_and_log_output_truncates_long_borg_error_output():
    flexmock(module).ERROR_OUTPUT_MAX_LINE_COUNT = 0
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('borg_command').and_return(False)

    with pytest.raises(subprocess.CalledProcessError) as error:
        module.execute_and_log_output(
            ['grep'], output_log_level=logging.INFO, shell=False, environment=None
        )

    assert error.value.returncode == 2
    assert error.value.output.startswith('...')


def test_execute_and_log_output_with_no_output_logs_nothing():
    flexmock(module.logger).should_receive('log').never()
    flexmock(module).should_receive('borg_command').and_return(False)

    module.execute_and_log_output(
        ['true'], output_log_level=logging.INFO, shell=False, environment=None
    )


def test_execute_and_log_output_with_error_exit_status_raises():
    flexmock(module.logger).should_receive('log')
    flexmock(module).should_receive('borg_command').and_return(False)

    with pytest.raises(subprocess.CalledProcessError):
        module.execute_and_log_output(
            ['grep'], output_log_level=logging.INFO, shell=False, environment=None
        )
