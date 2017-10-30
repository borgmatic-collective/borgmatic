import pytest

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


def test_apply_logical_validation_does_not_raise_if_archive_name_format_and_prefix_present():
    module.apply_logical_validation(
        'config.yaml',
        {
            'storage': {'archive_name_format': '{hostname}-{now}'},
            'retention': {'prefix': '{hostname}-'},
        },
    )


def test_apply_logical_validation_does_not_raise_otherwise():
    module.apply_logical_validation(
        'config.yaml',
        {
            'retention': {'keep_secondly': 1000},
        },
    )
