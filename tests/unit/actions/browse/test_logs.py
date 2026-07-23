from flexmock import flexmock

from borgmatic.actions.browse import logs as module


def test_rich_color_formatter_format_colors_log_record_based_on_level():
    formatted = module.Rich_color_formatter().format(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.ERROR,
                levelname='ERROR',
                msg='oh no',
            )
        ),
    )

    assert formatted == '[bright_red]oh no[/bright_red]'


def test_rich_color_formatter_format_includes_prefix():
    formatter = module.Rich_color_formatter()
    formatter.prefix = 'sup'
    formatted = formatter.format(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.ERROR,
                levelname='ERROR',
                msg='oh no',
            ),
        ),
    )

    assert formatted == '[bright_red]sup: oh no[/bright_red]'


def test_browse_log_handler_emit_from_worker_thread_calls_write_in_main_thread():
    flexmock(module.textual.worker).should_receive('get_current_worker')
    logs_widget = flexmock(write=lambda message: None, app=flexmock())
    flexmock(logs_widget.app).should_receive('call_from_thread').with_args(
        logs_widget.write, 'hi'
    ).once()

    module.Browse_log_handler(logs_widget).emit(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.DEBUG,
                levelname='DEBUG',
                msg='hi',
            ),
        ),
    )


def test_browse_log_handler_emit_from_main_thread_calls_write_directly():
    flexmock(module.textual.worker).should_receive('get_current_worker').and_raise(RuntimeError)
    logs_widget = flexmock(write=lambda message: None, app=flexmock())
    flexmock(logs_widget.app).should_receive('call_from_thread').never()
    flexmock(logs_widget).should_receive('write').with_args('hi').once()

    module.Browse_log_handler(logs_widget).emit(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.DEBUG,
                levelname='DEBUG',
                msg='hi',
            ),
        ),
    )


def test_browse_log_handler_emit_from_main_thread_with_no_active_app_does_not_raise():
    flexmock(module.textual.worker).should_receive('get_current_worker').and_raise(RuntimeError)
    logs_widget = flexmock(write=lambda message: None, app=flexmock())
    flexmock(logs_widget.app).should_receive('call_from_thread').never()
    flexmock(logs_widget).should_receive('write').with_args('hi').and_raise(
        module.textual._context.NoActiveAppError
    )

    module.Browse_log_handler(logs_widget).emit(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.DEBUG,
                levelname='DEBUG',
                msg='hi',
            ),
        ),
    )
