import logging

from flexmock import flexmock

from borgmatic.hooks.monitoring import healthchecks as module


def test_destroy_monitor_removes_healthchecks_handler():
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)
    module.borgmatic.hooks.monitoring.logs.add_handler(
        module.borgmatic.hooks.monitoring.logs.Forgetful_buffering_handler(
            identifier=module.HANDLER_IDENTIFIER, byte_capacity=100, log_level=1
        )
    )

    module.destroy_monitor(flexmock(), flexmock(), flexmock(), flexmock(), flexmock())

    assert logger.handlers == original_handlers


def test_destroy_monitor_without_healthchecks_handler_does_not_raise():
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)

    module.destroy_monitor(flexmock(), flexmock(), flexmock(), flexmock(), flexmock())

    assert logger.handlers == original_handlers
