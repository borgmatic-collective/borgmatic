import logging

import pytest
from flexmock import flexmock

from borgmatic import logger as module


@pytest.mark.parametrize('bool_val', (True, 'yes', 'on', '1', 'true', 'True', 1))
def test_to_bool_parses_true_values(bool_val):
    assert module.to_bool(bool_val)


@pytest.mark.parametrize('bool_val', (False, 'no', 'off', '0', 'false', 'False', 0))
def test_to_bool_parses_false_values(bool_val):
    assert not module.to_bool(bool_val)


def test_to_bool_passes_none_through():
    assert module.to_bool(None) is None


def test_should_do_markup_respects_no_color_value():
    assert module.should_do_markup(no_color=True) is False


def test_should_do_markup_respects_PY_COLORS_environment_variable():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=False) is True


def test_should_do_markup_prefers_no_color_value_to_PY_COLORS():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=True) is False


def test_should_do_markup_respects_stdout_tty_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)

    assert module.should_do_markup(no_color=False) is False


def test_should_do_markup_prefers_PY_COLORS_to_stdout_tty_value():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=False) is True


@pytest.mark.parametrize('method_name', ('critical', 'error', 'warn', 'info', 'debug'))
def test_borgmatic_logger_log_method_does_not_raise(method_name):
    flexmock(module).should_receive('color_text')
    flexmock(module.logging.Logger).should_receive(method_name)

    getattr(module.Borgmatic_logger('test'), method_name)(msg='hi')


def test_borgmatic_logger_handle_does_not_raise():
    flexmock(module).should_receive('color_text')
    flexmock(module.logging.Logger).should_receive('handle')

    module.Borgmatic_logger('test').handle(
        module.logging.makeLogRecord(dict(levelno=module.logging.CRITICAL, msg='hi'))
    )


def test_color_text_does_not_raise():
    module.color_text(module.colorama.Fore.RED, 'hi')


def test_color_text_without_color_does_not_raise():
    module.color_text(None, 'hi')


def test_configure_logging_probes_for_log_socket_on_linux():
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=tuple
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/var/run/syslog').and_return(False)
    syslog_handler = logging.handlers.SysLogHandler()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').with_args(
        address='/dev/log'
    ).and_return(syslog_handler).once()

    module.configure_logging(logging.INFO)


def test_configure_logging_probes_for_log_socket_on_macos():
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=tuple
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/var/run/syslog').and_return(True)
    syslog_handler = logging.handlers.SysLogHandler()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').with_args(
        address='/var/run/syslog'
    ).and_return(syslog_handler).once()

    module.configure_logging(logging.INFO)


def test_configure_logging_sets_global_logger_to_most_verbose_log_level():
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=tuple
    ).once()
    flexmock(module.os.path).should_receive('exists').and_return(False)

    module.configure_logging(console_log_level=logging.INFO, syslog_log_level=logging.DEBUG)


def test_configure_logging_skips_syslog_if_not_found():
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=tuple
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()

    module.configure_logging(console_log_level=logging.INFO)
