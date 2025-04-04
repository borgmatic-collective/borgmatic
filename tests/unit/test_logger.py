import logging
import sys

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


def test_interactive_console_false_when_not_isatty(capsys):
    with capsys.disabled():
        flexmock(module.sys.stderr).should_receive('isatty').and_return(False)

        assert module.interactive_console() is False


def test_interactive_console_false_when_TERM_is_dumb(capsys):
    with capsys.disabled():
        flexmock(module.sys.stderr).should_receive('isatty').and_return(True)
        flexmock(module.os.environ).should_receive('get').with_args('TERM').and_return('dumb')

        assert module.interactive_console() is False


def test_interactive_console_true_when_isatty_and_TERM_is_not_dumb(capsys):
    with capsys.disabled():
        flexmock(module.sys.stderr).should_receive('isatty').and_return(True)
        flexmock(module.os.environ).should_receive('get').with_args('TERM').and_return('smart')

        assert module.interactive_console() is True


def test_should_do_markup_respects_json_enabled_value():
    flexmock(module.os.environ).should_receive('get').never()
    flexmock(module).should_receive('interactive_console').never()
    assert module.should_do_markup(configs={}, json_enabled=True) is False


def test_should_do_markup_respects_config_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)
    flexmock(module).should_receive('interactive_console').never()
    assert (
        module.should_do_markup(configs={'foo.yaml': {'color': False}}, json_enabled=False) is False
    )

    flexmock(module).should_receive('interactive_console').and_return(True).once()
    assert (
        module.should_do_markup(configs={'foo.yaml': {'color': True}}, json_enabled=False) is True
    )


def test_should_do_markup_prefers_any_false_config_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)
    flexmock(module).should_receive('interactive_console').never()

    assert (
        module.should_do_markup(
            configs={
                'foo.yaml': {'color': True},
                'bar.yaml': {'color': False},
            },
            json_enabled=False,
        )
        is False
    )


def test_should_do_markup_respects_PY_COLORS_environment_variable():
    flexmock(module.os.environ).should_receive('get').with_args('PY_COLORS', None).and_return(
        'True'
    )
    flexmock(module.os.environ).should_receive('get').with_args('NO_COLOR', None).and_return(None)

    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(configs={}, json_enabled=False) is True


def test_should_do_markup_prefers_json_enabled_value_to_config_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)
    flexmock(module).should_receive('interactive_console').never()

    assert (
        module.should_do_markup(configs={'foo.yaml': {'color': True}}, json_enabled=True) is False
    )


def test_should_do_markup_prefers_config_value_to_environment_variables():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)
    flexmock(module).should_receive('interactive_console').never()

    assert (
        module.should_do_markup(configs={'foo.yaml': {'color': False}}, json_enabled=False) is False
    )


def test_should_do_markup_prefers_no_color_value_to_environment_variables():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)
    flexmock(module).should_receive('interactive_console').never()

    assert module.should_do_markup(configs={}, json_enabled=False) is False


def test_should_do_markup_respects_interactive_console_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)
    flexmock(module).should_receive('interactive_console').and_return(True)

    assert module.should_do_markup(configs={}, json_enabled=False) is True


def test_should_do_markup_prefers_PY_COLORS_to_interactive_console_value():
    flexmock(module.os.environ).should_receive('get').with_args('PY_COLORS', None).and_return(
        'True'
    )
    flexmock(module.os.environ).should_receive('get').with_args('NO_COLOR', None).and_return(None)
    flexmock(module).should_receive('to_bool').and_return(True)
    flexmock(module).should_receive('interactive_console').never()

    assert module.should_do_markup(configs={}, json_enabled=False) is True


def test_should_do_markup_prefers_NO_COLOR_to_interactive_console_value():
    flexmock(module.os.environ).should_receive('get').with_args('PY_COLORS', None).and_return(None)
    flexmock(module.os.environ).should_receive('get').with_args('NO_COLOR', None).and_return('True')
    flexmock(module).should_receive('interactive_console').never()

    assert module.should_do_markup(configs={}, json_enabled=False) is False


def test_should_do_markup_respects_NO_COLOR_environment_variable():
    flexmock(module.os.environ).should_receive('get').with_args('NO_COLOR', None).and_return('True')
    flexmock(module.os.environ).should_receive('get').with_args('PY_COLORS', None).and_return(None)
    flexmock(module).should_receive('interactive_console').never()

    assert module.should_do_markup(configs={}, json_enabled=False) is False


def test_should_do_markup_ignores_empty_NO_COLOR_environment_variable():
    flexmock(module.os.environ).should_receive('get').with_args('NO_COLOR', None).and_return('')
    flexmock(module.os.environ).should_receive('get').with_args('PY_COLORS', None).and_return(None)
    flexmock(module).should_receive('interactive_console').and_return(True)

    assert module.should_do_markup(configs={}, json_enabled=False) is True


def test_should_do_markup_prefers_NO_COLOR_to_PY_COLORS():
    flexmock(module.os.environ).should_receive('get').with_args('PY_COLORS', None).and_return(
        'True'
    )
    flexmock(module.os.environ).should_receive('get').with_args('NO_COLOR', None).and_return(
        'SomeValue'
    )
    flexmock(module).should_receive('interactive_console').never()

    assert module.should_do_markup(configs={}, json_enabled=False) is False


def test_multi_stream_handler_logs_to_handler_for_log_level():
    error_handler = flexmock()
    error_handler.should_receive('emit').once()
    info_handler = flexmock()

    multi_handler = module.Multi_stream_handler(
        {module.logging.ERROR: error_handler, module.logging.INFO: info_handler}
    )
    multi_handler.emit(flexmock(levelno=module.logging.ERROR))


def test_console_color_formatter_format_includes_log_message():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    plain_message = 'uh oh'
    flexmock(module.logging.Formatter).should_receive('format').and_return(plain_message)
    record = flexmock(levelno=logging.CRITICAL)

    colored_message = module.Console_color_formatter().format(record)

    assert colored_message != plain_message
    assert plain_message in colored_message


def test_color_text_does_not_raise():
    flexmock(module).should_receive('ansi_escape_code').and_return('blah')

    module.color_text(module.Color.RED, 'hi')


def test_color_text_without_color_does_not_raise():
    flexmock(module).should_receive('ansi_escape_code').and_return('blah')

    module.color_text(None, 'hi')


def test_add_logging_level_adds_level_name_and_sets_global_attributes_and_methods():
    logger = flexmock()
    flexmock(module.logging).should_receive('getLoggerClass').and_return(logger)
    flexmock(module.logging).should_receive('addLevelName').with_args(99, 'PLAID')
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_call('setattr')
    builtins.should_receive('setattr').with_args(module.logging, 'PLAID', 99).once()
    builtins.should_receive('setattr').with_args(logger, 'plaid', object).once()
    builtins.should_receive('setattr').with_args(logging, 'plaid', object).once()

    module.add_logging_level('PLAID', 99)


def test_add_logging_level_skips_global_setting_if_already_set():
    logger = flexmock()
    flexmock(module.logging).should_receive('getLoggerClass').and_return(logger)
    flexmock(module.logging).PLAID = 99
    flexmock(logger).plaid = flexmock()
    flexmock(logging).plaid = flexmock()
    flexmock(module.logging).should_receive('addLevelName').never()
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_call('setattr')
    builtins.should_receive('setattr').with_args(module.logging, 'PLAID', 99).never()
    builtins.should_receive('setattr').with_args(logger, 'plaid', object).never()
    builtins.should_receive('setattr').with_args(logging, 'plaid', object).never()

    module.add_logging_level('PLAID', 99)


def test_get_log_prefix_gets_prefix_from_first_handler_formatter_with_prefix():
    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(
            handlers=[
                flexmock(formatter=flexmock()),
                flexmock(formatter=flexmock(prefix='myprefix')),
            ],
            removeHandler=lambda handler: None,
        )
    )

    assert module.get_log_prefix() == 'myprefix'


def test_get_log_prefix_with_no_handlers_does_not_raise():
    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(
            handlers=[],
            removeHandler=lambda handler: None,
        )
    )

    assert module.get_log_prefix() is None


def test_get_log_prefix_with_no_formatters_does_not_raise():
    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(
            handlers=[
                flexmock(formatter=None),
                flexmock(formatter=None),
            ],
            removeHandler=lambda handler: None,
        )
    )

    assert module.get_log_prefix() is None


def test_get_log_prefix_with_no_prefix_does_not_raise():
    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(
            handlers=[
                flexmock(
                    formatter=flexmock(),
                ),
            ],
            removeHandler=lambda handler: None,
        )
    )

    assert module.get_log_prefix() is None


def test_set_log_prefix_updates_all_handler_formatters():
    formatters = (
        flexmock(prefix=None),
        flexmock(prefix=None),
    )

    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(
            handlers=[
                flexmock(
                    formatter=formatters[0],
                ),
                flexmock(
                    formatter=formatters[1],
                ),
            ],
            removeHandler=lambda handler: None,
        )
    )

    module.set_log_prefix('myprefix')

    for formatter in formatters:
        assert formatter.prefix == 'myprefix'


def test_set_log_prefix_skips_handlers_without_a_formatter():
    formatter = flexmock(prefix=None)

    flexmock(module.logging).should_receive('getLogger').and_return(
        flexmock(
            handlers=[
                flexmock(
                    formatter=None,
                ),
                flexmock(
                    formatter=formatter,
                ),
            ],
            removeHandler=lambda handler: None,
        )
    )

    module.set_log_prefix('myprefix')

    assert formatter.prefix == 'myprefix'


def test_log_prefix_sets_prefix_and_then_restores_no_prefix_after():
    flexmock(module).should_receive('get_log_prefix').and_return(None)
    flexmock(module).should_receive('set_log_prefix').with_args('myprefix').once()
    flexmock(module).should_receive('set_log_prefix').with_args(None).once()

    with module.Log_prefix('myprefix'):
        pass


def test_log_prefix_sets_prefix_and_then_restores_original_prefix_after():
    flexmock(module).should_receive('get_log_prefix').and_return('original')
    flexmock(module).should_receive('set_log_prefix').with_args('myprefix').once()
    flexmock(module).should_receive('set_log_prefix').with_args('original').once()

    with module.Log_prefix('myprefix'):
        pass


def test_delayed_logging_handler_should_flush_without_targets_returns_false():
    handler = module.Delayed_logging_handler()

    assert handler.shouldFlush(flexmock()) is False


def test_delayed_logging_handler_should_flush_with_targets_returns_true():
    handler = module.Delayed_logging_handler()
    handler.targets = [flexmock()]

    assert handler.shouldFlush(flexmock()) is True


def test_delayed_logging_handler_flush_without_targets_does_not_raise():
    handler = module.Delayed_logging_handler()
    flexmock(handler).should_receive('acquire')
    flexmock(handler).should_receive('release')

    handler.flush()


def test_delayed_logging_handler_flush_with_empty_buffer_does_not_raise():
    handler = module.Delayed_logging_handler()
    flexmock(handler).should_receive('acquire')
    flexmock(handler).should_receive('release')
    handler.targets = [flexmock()]

    handler.flush()


def test_delayed_logging_handler_flush_forwards_each_record_to_each_target():
    handler = module.Delayed_logging_handler()
    flexmock(handler).should_receive('acquire')
    flexmock(handler).should_receive('release')
    handler.targets = [flexmock(level=logging.DEBUG), flexmock(level=logging.DEBUG)]
    handler.buffer = [flexmock(levelno=logging.DEBUG), flexmock(levelno=logging.DEBUG)]
    handler.targets[0].should_receive('handle').with_args(handler.buffer[0]).once()
    handler.targets[1].should_receive('handle').with_args(handler.buffer[0]).once()
    handler.targets[0].should_receive('handle').with_args(handler.buffer[1]).once()
    handler.targets[1].should_receive('handle').with_args(handler.buffer[1]).once()

    handler.flush()

    assert handler.buffer == []


def test_delayed_logging_handler_flush_skips_forwarding_when_log_record_is_too_low_for_target():
    handler = module.Delayed_logging_handler()
    flexmock(handler).should_receive('acquire')
    flexmock(handler).should_receive('release')
    handler.targets = [flexmock(level=logging.INFO), flexmock(level=logging.DEBUG)]
    handler.buffer = [flexmock(levelno=logging.DEBUG), flexmock(levelno=logging.INFO)]
    handler.targets[0].should_receive('handle').with_args(handler.buffer[0]).never()
    handler.targets[1].should_receive('handle').with_args(handler.buffer[0]).once()
    handler.targets[0].should_receive('handle').with_args(handler.buffer[1]).once()
    handler.targets[1].should_receive('handle').with_args(handler.buffer[1]).once()

    handler.flush()

    assert handler.buffer == []


def test_flush_delayed_logging_without_handlers_does_not_raise():
    root_logger = flexmock(handlers=[])
    root_logger.should_receive('removeHandler')
    flexmock(module.logging).should_receive('getLogger').and_return(root_logger)

    module.flush_delayed_logging([flexmock()])


def test_flush_delayed_logging_without_delayed_logging_handler_does_not_raise():
    root_logger = flexmock(handlers=[flexmock()])
    root_logger.should_receive('removeHandler')
    flexmock(module.logging).should_receive('getLogger').and_return(root_logger)

    module.flush_delayed_logging([flexmock()])


def test_flush_delayed_logging_flushes_delayed_logging_handler():
    delayed_logging_handler = module.Delayed_logging_handler()
    root_logger = flexmock(handlers=[delayed_logging_handler])
    flexmock(module.logging).should_receive('getLogger').and_return(root_logger)
    flexmock(delayed_logging_handler).should_receive('flush').once()
    root_logger.should_receive('removeHandler')

    module.flush_delayed_logging([flexmock()])


def test_configure_logging_with_syslog_log_level_probes_for_log_socket_on_linux():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)
    flexmock(module).should_receive('interactive_console').and_return(False)
    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(True)
    syslog_handler = logging.handlers.SysLogHandler()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').with_args(
        address='/dev/log'
    ).and_return(syslog_handler).once()

    module.configure_logging(logging.INFO, syslog_log_level=logging.DEBUG)


def test_configure_logging_with_syslog_log_level_probes_for_log_socket_on_macos():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)
    flexmock(module).should_receive('interactive_console').and_return(False)
    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/var/run/syslog').and_return(True)
    syslog_handler = logging.handlers.SysLogHandler()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').with_args(
        address='/var/run/syslog'
    ).and_return(syslog_handler).once()

    module.configure_logging(logging.INFO, syslog_log_level=logging.DEBUG)


def test_configure_logging_with_syslog_log_level_probes_for_log_socket_on_freebsd():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)
    flexmock(module).should_receive('interactive_console').and_return(False)
    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/var/run/syslog').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/var/run/log').and_return(True)
    syslog_handler = logging.handlers.SysLogHandler()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').with_args(
        address='/var/run/log'
    ).and_return(syslog_handler).once()

    module.configure_logging(logging.INFO, syslog_log_level=logging.DEBUG)


def test_configure_logging_without_syslog_log_level_skips_syslog():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)
    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()

    module.configure_logging(console_log_level=logging.INFO)


def test_configure_logging_skips_syslog_if_not_found():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)
    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()

    module.configure_logging(console_log_level=logging.INFO, syslog_log_level=logging.DEBUG)


def test_configure_logging_skips_log_file_if_log_file_logging_is_disabled():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).DISABLED = module.DISABLED
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)

    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()
    flexmock(module.logging.handlers).should_receive('WatchedFileHandler').never()

    module.configure_logging(
        console_log_level=logging.INFO, log_file_log_level=logging.DISABLED, log_file='/tmp/logfile'
    )


def test_configure_logging_to_log_file_instead_of_syslog():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)

    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()
    file_handler = logging.handlers.WatchedFileHandler('/tmp/logfile')
    flexmock(module.logging.handlers).should_receive('WatchedFileHandler').with_args(
        '/tmp/logfile'
    ).and_return(file_handler).once()

    module.configure_logging(
        console_log_level=logging.INFO,
        syslog_log_level=logging.DISABLED,
        log_file_log_level=logging.DEBUG,
        log_file='/tmp/logfile',
    )


def test_configure_logging_to_both_log_file_and_syslog():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)

    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(True)
    syslog_handler = logging.handlers.SysLogHandler()
    flexmock(module.logging.handlers).should_receive('SysLogHandler').with_args(
        address='/dev/log'
    ).and_return(syslog_handler).once()
    file_handler = logging.handlers.WatchedFileHandler('/tmp/logfile')
    flexmock(module.logging.handlers).should_receive('WatchedFileHandler').with_args(
        '/tmp/logfile'
    ).and_return(file_handler).once()

    module.configure_logging(
        console_log_level=logging.INFO,
        syslog_log_level=logging.DEBUG,
        log_file_log_level=logging.DEBUG,
        log_file='/tmp/logfile',
    )


def test_configure_logging_to_log_file_formats_with_custom_log_format():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    flexmock(module).should_receive('Log_prefix_formatter').with_args(
        '{message}',  # noqa: FS003
    ).once()
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)

    flexmock(module).should_receive('interactive_console').and_return(False)
    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.DEBUG, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').with_args('/dev/log').and_return(True)
    flexmock(module.logging.handlers).should_receive('SysLogHandler').never()
    file_handler = logging.handlers.WatchedFileHandler('/tmp/logfile')
    flexmock(module.logging.handlers).should_receive('WatchedFileHandler').with_args(
        '/tmp/logfile'
    ).and_return(file_handler).once()

    module.configure_logging(
        console_log_level=logging.INFO,
        log_file_log_level=logging.DEBUG,
        log_file='/tmp/logfile',
        log_file_format='{message}',  # noqa: FS003
    )


def test_configure_logging_skips_log_file_if_argument_is_none():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)

    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.logging.handlers).should_receive('WatchedFileHandler').never()

    module.configure_logging(console_log_level=logging.INFO, log_file=None)


def test_configure_logging_uses_console_no_color_formatter_if_color_disabled():
    flexmock(module).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.ANSWER
    fake_formatter = flexmock()
    flexmock(module).should_receive('Console_color_formatter').never()
    flexmock(module).should_receive('Log_prefix_formatter').and_return(fake_formatter)
    multi_stream_handler = flexmock(setLevel=lambda level: None, level=logging.INFO)
    multi_stream_handler.should_receive('setFormatter').with_args(fake_formatter).once()
    flexmock(module).should_receive('Multi_stream_handler').and_return(multi_stream_handler)

    flexmock(module).should_receive('flush_delayed_logging')
    flexmock(module.logging).should_receive('basicConfig').with_args(
        level=logging.INFO, handlers=list
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.logging.handlers).should_receive('WatchedFileHandler').never()

    module.configure_logging(console_log_level=logging.INFO, log_file=None, color_enabled=False)
