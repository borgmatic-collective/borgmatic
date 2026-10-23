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


def test_browse_log_handler_emit_posts_log_message_to_logs_widget():
    flexmock(module.Browse_log_handler).should_receive('format').and_return(flexmock)
    flexmock(module).should_receive('Log_message').and_return(flexmock())
    logs_widget = flexmock()
    logs_widget.should_receive('post_message').once()

    module.Browse_log_handler(logs_widget).emit(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.DEBUG,
                levelname='DEBUG',
                msg='hi',
            ),
        ),
    )


def test_browse_log_handler_emit_with_no_active_app_does_not_raise():
    flexmock(module.Browse_log_handler).should_receive('format').and_return(flexmock)
    flexmock(module).should_receive('Log_message').and_return(flexmock())
    logs_widget = flexmock()
    logs_widget.should_receive('post_message').and_raise(module.textual._context.NoActiveAppError)

    module.Browse_log_handler(logs_widget).emit(
        module.logging.makeLogRecord(
            dict(
                levelno=module.logging.DEBUG,
                levelname='DEBUG',
                msg='hi',
            ),
        ),
    )
