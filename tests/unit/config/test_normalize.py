import pytest

from borgmatic.config import normalize as module


@pytest.mark.parametrize(
    'config,expected_config',
    (
        (
            {'location': {'exclude_if_present': '.nobackup'}},
            {'location': {'exclude_if_present': ['.nobackup']}},
        ),
        (
            {'location': {'exclude_if_present': ['.nobackup']}},
            {'location': {'exclude_if_present': ['.nobackup']}},
        ),
        (
            {'location': {'source_directories': ['foo', 'bar']}},
            {'location': {'source_directories': ['foo', 'bar']}},
        ),
        ({'storage': {'compression': 'yes_please'}}, {'storage': {'compression': 'yes_please'}}),
    ),
)
def test_normalize_applies_hard_coded_normalization_to_config(config, expected_config):
    module.normalize(config)

    assert config == expected_config
