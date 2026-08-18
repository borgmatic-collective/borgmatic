import contextlib

from flexmock import flexmock

from borgmatic.actions.browse import logs as module


def test_log_to_widget_adds_our_handler_and_removes_default_handler():
    default_handler = module.borgmatic.logger.Multi_stream_handler({})
    root_logger = module.logging.getLogger()
    root_logger.addHandler(default_handler)
    browse_log_handler = None

    try:
        module.log_to_widget(flexmock())

        with contextlib.suppress(StopIteration):
            browse_log_handler = next(
                handler
                for handler in root_logger.handlers
                if isinstance(handler, module.Browse_log_handler)
            )

        assert browse_log_handler
    finally:
        if browse_log_handler:
            root_logger.removeHandler(browse_log_handler)

    assert not any(
        handler
        for handler in root_logger.handlers
        if isinstance(handler, module.borgmatic.logger.Multi_stream_handler)
    )


def test_logs_does_not_raise():
    module.Logs()
