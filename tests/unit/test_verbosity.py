import logging

import pytest
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
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logging).DISABLED = module.borgmatic.logger.DISABLED

    assert module.verbosity_to_log_level(module.VERBOSITY_ERROR) == logging.ERROR
    assert module.verbosity_to_log_level(module.VERBOSITY_ANSWER) == module.borgmatic.logger.ANSWER
    assert module.verbosity_to_log_level(module.VERBOSITY_SOME) == logging.INFO
    assert module.verbosity_to_log_level(module.VERBOSITY_LOTS) == logging.DEBUG
    assert module.verbosity_to_log_level(module.VERBOSITY_DISABLED) == logging.DISABLED


def test_verbosity_to_log_level_maps_unknown_verbosity_to_warning_level():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER

    assert module.verbosity_to_log_level('my pants') == logging.WARNING


@pytest.mark.parametrize(
    'option_name',
    (
        'verbosity',
        'syslog_verbosity',
        'log_file_verbosity',
        'monitoring_verbosity',
    ),
)
def test_get_verbosity_gets_maximum_verbosity_across_configurations(option_name):
    assert (
        module.get_verbosity(
            configs={
                'test1.yaml': {option_name: -1},
                'test2.yaml': {option_name: 2},
                'test3.yaml': {option_name: None},
            },
            option_name=option_name,
        )
        == 2
    )


@pytest.mark.parametrize(
    'option_name',
    (
        'verbosity',
        'syslog_verbosity',
        'log_file_verbosity',
        'monitoring_verbosity',
    ),
)
def test_get_verbosity_with_nothing_set_gets_default_verbosity(option_name):
    assert (
        module.get_verbosity(
            configs={
                'test1.yaml': {},
                'test2.yaml': {'other': 'thing'},
            },
            option_name=option_name,
        )
        == module.DEFAULT_VERBOSITIES[option_name]
    )


@pytest.mark.parametrize(
    'option_name',
    (
        'verbosity',
        'syslog_verbosity',
        'log_file_verbosity',
        'monitoring_verbosity',
    ),
)
def test_get_verbosity_with_no_configs_set_gets_default_verbosity(option_name):
    assert (
        module.get_verbosity(
            configs={},
            option_name=option_name,
        )
        == module.DEFAULT_VERBOSITIES[option_name]
    )
