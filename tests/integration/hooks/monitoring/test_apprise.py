import logging

from flexmock import flexmock

from borgmatic.hooks.monitoring import apprise as module


def test_destroy_monitor_removes_apprise_handler():
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)

    # Don't mess with the actual log level because it can impact downstream tests.
    flexmock(logger).should_receive('setLevel')
    module.borgmatic.hooks.monitoring.logs.add_handler(
        module.borgmatic.hooks.monitoring.logs.Forgetful_buffering_handler(
            identifier=module.HANDLER_IDENTIFIER,
            byte_capacity=100,
            log_level=1,
        ),
    )
    module.destroy_monitor(
        hook_config=flexmock(),
        config=flexmock(),
        monitoring_log_level=1,
        dry_run=False,
    )

    assert logger.handlers == original_handlers


def test_destroy_monitor_without_apprise_handler_does_not_raise():
    logger = logging.getLogger()
    original_handlers = list(logger.handlers)

    # Don't mess with the actual log level because it can impact downstream tests.
    flexmock(logger).should_receive('setLevel')
    module.destroy_monitor(
        hook_config=flexmock(),
        config=flexmock(),
        monitoring_log_level=1,
        dry_run=False,
    )

    assert logger.handlers == original_handlers
