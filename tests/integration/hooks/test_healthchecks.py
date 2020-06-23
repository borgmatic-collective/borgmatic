import logging

from flexmock import flexmock

from borgmatic.hooks import healthchecks as module


def test_destroy_monitor_removes_healthchecks_handler():
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)
    logger.addHandler(module.Forgetful_buffering_handler(byte_capacity=100, log_level=1))

    module.destroy_monitor(flexmock(), flexmock(), flexmock(), flexmock())

    assert logger.handlers == original_handlers


def test_destroy_monitor_without_healthchecks_handler_does_not_raise():
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)

    module.destroy_monitor(flexmock(), flexmock(), flexmock(), flexmock())

    assert logger.handlers == original_handlers
