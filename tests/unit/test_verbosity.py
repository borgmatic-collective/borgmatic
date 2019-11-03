import logging

from flexmock import flexmock

from borgmatic import verbosity as module


def insert_logging_mock(log_level):
    '''
    Mock the isEnabledFor from Python logging.
    '''
    logging = flexmock(module.logging.Logger)
    logging.should_receive('isEnabledFor').replace_with(lambda level: level >= log_level)
    logging.should_receive('getEffectiveLevel').replace_with(lambda: log_level)


def test_verbosity_to_log_level_maps_known_verbosity_to_log_level():
    assert module.verbosity_to_log_level(module.VERBOSITY_SOME) == logging.INFO
    assert module.verbosity_to_log_level(module.VERBOSITY_LOTS) == logging.DEBUG
    assert module.verbosity_to_log_level(module.VERBOSITY_ERROR) == logging.ERROR


def test_verbosity_to_log_level_maps_unknown_verbosity_to_warning_level():
    assert module.verbosity_to_log_level('my pants') == logging.WARNING
