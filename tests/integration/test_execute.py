import logging
import subprocess

import pytest
from flexmock import flexmock

from borgmatic import execute as module


def test_execute_and_log_output_logs_each_line_separately():
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'hi').once()
    flexmock(module.logger).should_receive('log').with_args(logging.INFO, 'there').once()

    module.execute_and_log_output(['echo', 'hi'], output_log_level=logging.INFO, shell=False)
    module.execute_and_log_output(['echo', 'there'], output_log_level=logging.INFO, shell=False)


def test_execute_and_log_output_logs_borg_error_as_error():
    flexmock(module.logger).should_receive('error').with_args('borg: error: oopsie').once()

    module.execute_and_log_output(
        ['echo', 'borg: error: oopsie'], output_log_level=logging.INFO, shell=False
    )


def test_execute_and_log_output_with_no_output_logs_nothing():
    flexmock(module.logger).should_receive('log').never()

    module.execute_and_log_output(['true'], output_log_level=logging.INFO, shell=False)


def test_execute_and_log_output_with_error_exit_status_raises():
    flexmock(module.logger).should_receive('log').never()

    with pytest.raises(subprocess.CalledProcessError):
        module.execute_and_log_output(['false'], output_log_level=logging.INFO, shell=False)
