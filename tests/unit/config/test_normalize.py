import pytest

from borgmatic.config import normalize as module


@pytest.mark.parametrize(
    'config,expected_config,produces_logs',
    (
        (
            {'location': {'exclude_if_present': '.nobackup'}},
            {'location': {'exclude_if_present': ['.nobackup']}},
            False,
        ),
        (
            {'location': {'exclude_if_present': ['.nobackup']}},
            {'location': {'exclude_if_present': ['.nobackup']}},
            False,
        ),
        (
            {'location': {'source_directories': ['foo', 'bar']}},
            {'location': {'source_directories': ['foo', 'bar']}},
            False,
        ),
        (
            {'storage': {'compression': 'yes_please'}},
            {'storage': {'compression': 'yes_please'}},
            False,
        ),
        (
            {'hooks': {'healthchecks': 'https://example.com'}},
            {'hooks': {'healthchecks': {'ping_url': 'https://example.com'}}},
            False,
        ),
        (
            {'hooks': {'cronitor': 'https://example.com'}},
            {'hooks': {'cronitor': {'ping_url': 'https://example.com'}}},
            False,
        ),
        (
            {'hooks': {'pagerduty': 'https://example.com'}},
            {'hooks': {'pagerduty': {'integration_key': 'https://example.com'}}},
            False,
        ),
        (
            {'hooks': {'cronhub': 'https://example.com'}},
            {'hooks': {'cronhub': {'ping_url': 'https://example.com'}}},
            False,
        ),
        (
            {'consistency': {'checks': ['archives']}},
            {'consistency': {'checks': [{'name': 'archives'}]}},
            False,
        ),
        (
            {'location': {'repositories': ['foo@bar:/repo']}},
            {'location': {'repositories': ['ssh://foo@bar/repo']}},
            True,
        ),
        (
            {'location': {'repositories': ['foo@bar:repo']}},
            {'location': {'repositories': ['ssh://foo@bar/./repo']}},
            True,
        ),
        (
            {'location': {'repositories': ['foo@bar:~/repo']}},
            {'location': {'repositories': ['ssh://foo@bar/~/repo']}},
            True,
        ),
        (
            {'location': {'repositories': ['ssh://foo@bar/repo']}},
            {'location': {'repositories': ['ssh://foo@bar/repo']}},
            False,
        ),
    ),
)
def test_normalize_applies_hard_coded_normalization_to_config(
    config, expected_config, produces_logs
):
    logs = module.normalize('test.yaml', config)

    assert config == expected_config

    if produces_logs:
        assert logs
    else:
        assert logs == []
