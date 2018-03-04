import logging

from borgmatic import verbosity as module


def test_verbosity_to_log_level_maps_known_verbosity_to_log_level():
    assert module.verbosity_to_log_level(module.VERBOSITY_SOME) == logging.INFO


def test_verbosity_to_log_level_maps_unknown_verbosity_to_warning_level():
    assert module.verbosity_to_log_level('my pants') == logging.WARNING
