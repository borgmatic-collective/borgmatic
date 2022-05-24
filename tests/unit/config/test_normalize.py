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
        (
            {'hooks': {'healthchecks': 'https://example.com'}},
            {'hooks': {'healthchecks': {'ping_url': 'https://example.com'}}},
        ),
        (
            {'hooks': {'cronitor': 'https://example.com'}},
            {'hooks': {'cronitor': {'ping_url': 'https://example.com'}}},
        ),
        (
            {'hooks': {'pagerduty': 'https://example.com'}},
            {'hooks': {'pagerduty': {'integration_key': 'https://example.com'}}},
        ),
        (
            {'hooks': {'cronhub': 'https://example.com'}},
            {'hooks': {'cronhub': {'ping_url': 'https://example.com'}}},
        ),
    ),
)
def test_normalize_applies_hard_coded_normalization_to_config(config, expected_config):
    module.normalize(config)

    assert config == expected_config
