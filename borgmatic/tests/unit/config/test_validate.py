import pytest
from flexmock import flexmock

from borgmatic.config import validate as module


def test_validation_error_str_contains_error_messages_and_config_filename():
    error = module.Validation_error('config.yaml', ('oops', 'uh oh'))

    result = str(error)

    assert 'config.yaml' in result
    assert 'oops' in result
    assert 'uh oh' in result


def test_apply_logical_validation_raises_if_archive_name_format_present_without_prefix():
    with pytest.raises(module.Validation_error):
        module.apply_logical_validation(
            'config.yaml',
            {
                'storage': {'archive_name_format': '{hostname}-{now}'},
                'retention': {'keep_daily': 7},
            },
        )

def test_apply_logical_validation_raises_if_archive_name_format_present_without_retention_prefix():
    with pytest.raises(module.Validation_error):
        module.apply_logical_validation(
            'config.yaml',
            {
                'storage': {'archive_name_format': '{hostname}-{now}'},
                'retention': {'keep_daily': 7},
                'consistency': {'prefix': '{hostname}-'}
            },
        )


def test_apply_logical_validation_warns_if_archive_name_format_present_without_consistency_prefix():
    logger = flexmock(module.logger)
    logger.should_receive('warning').once()

    module.apply_logical_validation(
        'config.yaml',
        {
            'storage': {'archive_name_format': '{hostname}-{now}'},
            'retention': {'prefix': '{hostname}-'},
            'consistency': {},
        },
    )


def test_apply_logical_validation_does_not_raise_or_warn_if_archive_name_format_and_prefix_present():
    logger = flexmock(module.logger)
    logger.should_receive('warning').never()

    module.apply_logical_validation(
        'config.yaml',
        {
            'storage': {'archive_name_format': '{hostname}-{now}'},
            'retention': {'prefix': '{hostname}-'},
            'consistency': {'prefix': '{hostname}-'}
        },
    )


def test_apply_logical_validation_does_not_raise_otherwise():
    module.apply_logical_validation(
        'config.yaml',
        {
            'retention': {'keep_secondly': 1000},
        },
    )
