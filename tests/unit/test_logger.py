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
    assert module.should_do_markup(no_color=True, configs={}) is False


def test_should_do_markup_respects_config_value():
    assert (
        module.should_do_markup(no_color=False, configs={'foo.yaml': {'output': {'color': False}}})
        is False
    )


def test_should_do_markup_prefers_any_false_config_value():
    assert (
        module.should_do_markup(
            no_color=False,
            configs={
                'foo.yaml': {'output': {'color': True}},
                'bar.yaml': {'output': {'color': False}},
            },
        )
        is False
    )


def test_should_do_markup_respects_PY_COLORS_environment_variable():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=False, configs={}) is True


def test_should_do_markup_prefers_no_color_value_to_config_value():
    assert (
        module.should_do_markup(no_color=True, configs={'foo.yaml': {'output': {'color': True}}})
        is False
    )


def test_should_do_markup_prefers_config_value_to_PY_COLORS():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert (
        module.should_do_markup(no_color=False, configs={'foo.yaml': {'output': {'color': False}}})
        is False
    )


def test_should_do_markup_prefers_no_color_value_to_PY_COLORS():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=True, configs={}) is False


def test_should_do_markup_respects_stdout_tty_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)

    assert module.should_do_markup(no_color=False, configs={}) is False


def test_should_do_markup_prefers_PY_COLORS_to_stdout_tty_value():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=False, configs={}) is True


def test_console_color_formatter_format_includes_log_message():
    plain_message = 'uh oh'
    record = flexmock(levelno=logging.CRITICAL, msg=plain_message)

    colored_message = module.Console_color_formatter().format(record)

    assert colored_message != plain_message
    assert plain_message in colored_message


def test_color_text_does_not_raise():
    module.color_text(module.colorama.Fore.RED, 'hi')


def test_color_text_without_color_does_not_raise():
    module.color_text(None, 'hi')


def test_configure_logging_probes_for_log_socket_on_linux():
    flexmock(module).should_receive('Console_color_formatter')
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
    flexmock(module).should_receive('Console_color_formatter')
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
    flexmock(module).should_receive('Console_color_formatter')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=tuple
    ).once()
    flexmock(module.os.path).should_receive('exists').and_return(False)

    module.configure_logging(console_log_level=logging.INFO, syslog_log_level=logging.DEBUG)


def test_configure_logging_skips_syslog_if_not_found():
    flexmock(module).should_receive('Console_color_formatter')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=tuple
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()

    module.configure_logging(console_log_level=logging.INFO)
