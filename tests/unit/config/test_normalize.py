import pytest
from flexmock import flexmock

from borgmatic.config import normalize as module


@pytest.mark.parametrize(
    'config,expected_config,produces_logs',
    (
        (
            {'location': {'foo': 'bar', 'baz': 'quux'}},
            {'foo': 'bar', 'baz': 'quux'},
            True,
        ),
        (
            {'retention': {'foo': 'bar', 'baz': 'quux'}},
            {'foo': 'bar', 'baz': 'quux'},
            True,
        ),
        (
            {'consistency': {'foo': 'bar', 'baz': 'quux'}},
            {'foo': 'bar', 'baz': 'quux'},
            True,
        ),
        (
            {'output': {'foo': 'bar', 'baz': 'quux'}},
            {'foo': 'bar', 'baz': 'quux'},
            True,
        ),
        (
            {'hooks': {'foo': 'bar', 'baz': 'quux'}},
            {'foo': 'bar', 'baz': 'quux'},
            True,
        ),
        (
            {'location': {'foo': 'bar'}, 'storage': {'baz': 'quux'}},
            {'foo': 'bar', 'baz': 'quux'},
            True,
        ),
        (
            {'foo': 'bar', 'baz': 'quux'},
            {'foo': 'bar', 'baz': 'quux'},
            False,
        ),
        (
            {'location': {'prefix': 'foo'}, 'consistency': {'prefix': 'foo'}},
            {'prefix': 'foo'},
            True,
        ),
        (
            {'location': {'prefix': 'foo'}, 'consistency': {'prefix': 'foo'}},
            {'prefix': 'foo'},
            True,
        ),
        (
            {'location': {'prefix': 'foo'}, 'consistency': {'bar': 'baz'}},
            {'prefix': 'foo', 'bar': 'baz'},
            True,
        ),
        (
            {'storage': {'umask': 'foo'}, 'hooks': {'umask': 'foo'}},
            {'umask': 'foo'},
            True,
        ),
        (
            {'storage': {'umask': 'foo'}, 'hooks': {'umask': 'foo'}},
            {'umask': 'foo'},
            True,
        ),
        (
            {'storage': {'umask': 'foo'}, 'hooks': {'bar': 'baz'}},
            {'umask': 'foo', 'bar': 'baz'},
            True,
        ),
        (
            {'location': {'bar': 'baz'}, 'consistency': {'prefix': 'foo'}},
            {'bar': 'baz', 'prefix': 'foo'},
            True,
        ),
        (
            {'location': {}, 'consistency': {'prefix': 'foo'}},
            {'prefix': 'foo'},
            True,
        ),
        (
            {},
            {},
            False,
        ),
    ),
)
def test_normalize_sections_moves_section_options_to_global_scope(
    config, expected_config, produces_logs
):
    logs = module.normalize_sections('test.yaml', config)

    assert config == expected_config

    if produces_logs:
        assert logs
    else:
        assert logs == []


def test_normalize_sections_with_different_prefix_values_raises():
    config = {'location': {'prefix': 'foo'}, 'consistency': {'prefix': 'bar'}}

    with pytest.raises(ValueError):
        module.normalize_sections('test.yaml', config)


def test_normalize_sections_with_different_umask_values_raises():
    config = {'storage': {'umask': 'foo'}, 'hooks': {'umask': 'bar'}}

    with pytest.raises(ValueError):
        module.normalize_sections('test.yaml', config)


def test_normalize_sections_with_only_scalar_raises():
    config = 33

    with pytest.raises(ValueError):
        module.normalize_sections('test.yaml', config)


@pytest.mark.parametrize(
    'config,expected_config,produces_logs',
    (
        (
            {'before_actions': ['foo', 'bar'], 'after_actions': ['baz']},
            {
                'commands': [
                    {'before': 'repository', 'run': ['foo', 'bar']},
                    {'after': 'repository', 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'before_backup': ['foo', 'bar'], 'after_backup': ['baz']},
            {
                'commands': [
                    {'before': 'action', 'when': ['create'], 'run': ['foo', 'bar']},
                    {'after': 'action', 'when': ['create'], 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'before_prune': ['foo', 'bar'], 'after_prune': ['baz']},
            {
                'commands': [
                    {'before': 'action', 'when': ['prune'], 'run': ['foo', 'bar']},
                    {'after': 'action', 'when': ['prune'], 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'before_compact': ['foo', 'bar'], 'after_compact': ['baz']},
            {
                'commands': [
                    {'before': 'action', 'when': ['compact'], 'run': ['foo', 'bar']},
                    {'after': 'action', 'when': ['compact'], 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'before_check': ['foo', 'bar'], 'after_check': ['baz']},
            {
                'commands': [
                    {'before': 'action', 'when': ['check'], 'run': ['foo', 'bar']},
                    {'after': 'action', 'when': ['check'], 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'before_extract': ['foo', 'bar'], 'after_extract': ['baz']},
            {
                'commands': [
                    {'before': 'action', 'when': ['extract'], 'run': ['foo', 'bar']},
                    {'after': 'action', 'when': ['extract'], 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'on_error': ['foo', 'bar']},
            {
                'commands': [
                    {
                        'after': 'error',
                        'when': ['create', 'prune', 'compact', 'check'],
                        'run': ['foo', 'bar'],
                    },
                ]
            },
            True,
        ),
        (
            {'before_everything': ['foo', 'bar'], 'after_everything': ['baz']},
            {
                'commands': [
                    {'before': 'everything', 'when': ['create'], 'run': ['foo', 'bar']},
                    {'after': 'everything', 'when': ['create'], 'run': ['baz']},
                ]
            },
            True,
        ),
        (
            {'other': 'options', 'unrelated_to': 'commands'},
            {'other': 'options', 'unrelated_to': 'commands'},
            False,
        ),
    ),
)
def test_normalize_commands_moves_individual_command_hooks_to_unified_commands(
    config, expected_config, produces_logs
):
    flexmock(module).should_receive('make_command_hook_deprecation_log').and_return(flexmock())

    logs = module.normalize_commands('test.yaml', config)

    assert config == expected_config

    if produces_logs:
        assert logs
    else:
        assert logs == []


@pytest.mark.parametrize(
    'config,expected_config,produces_logs',
    (
        (
            {'exclude_if_present': '.nobackup'},
            {'exclude_if_present': ['.nobackup']},
            True,
        ),
        (
            {'exclude_if_present': ['.nobackup']},
            {'exclude_if_present': ['.nobackup']},
            False,
        ),
        (
            {'store_config_files': False},
            {'bootstrap': {'store_config_files': False}},
            True,
        ),
        (
            {'source_directories': ['foo', 'bar']},
            {'source_directories': ['foo', 'bar']},
            False,
        ),
        (
            {'compression': 'yes_please'},
            {'compression': 'yes_please'},
            False,
        ),
        (
            {'healthchecks': 'https://example.com'},
            {'healthchecks': {'ping_url': 'https://example.com'}},
            True,
        ),
        (
            {'cronitor': 'https://example.com'},
            {'cronitor': {'ping_url': 'https://example.com'}},
            True,
        ),
        (
            {'pagerduty': 'https://example.com'},
            {'pagerduty': {'integration_key': 'https://example.com'}},
            True,
        ),
        (
            {'cronhub': 'https://example.com'},
            {'cronhub': {'ping_url': 'https://example.com'}},
            True,
        ),
        (
            {'checks': ['archives']},
            {'checks': [{'name': 'archives'}]},
            True,
        ),
        (
            {'checks': ['archives']},
            {'checks': [{'name': 'archives'}]},
            True,
        ),
        (
            {'numeric_owner': False},
            {'numeric_ids': False},
            True,
        ),
        (
            {'bsd_flags': False},
            {'flags': False},
            True,
        ),
        (
            {'remote_rate_limit': False},
            {'upload_rate_limit': False},
            True,
        ),
        (
            {'repositories': ['foo@bar:/repo']},
            {'repositories': [{'path': 'ssh://foo@bar/repo'}]},
            True,
        ),
        (
            {'repositories': ['foo@bar:repo']},
            {'repositories': [{'path': 'ssh://foo@bar/./repo'}]},
            True,
        ),
        (
            {'repositories': ['foo@bar:~/repo']},
            {'repositories': [{'path': 'ssh://foo@bar/~/repo'}]},
            True,
        ),
        (
            {'repositories': ['ssh://foo@bar:1234/repo']},
            {'repositories': [{'path': 'ssh://foo@bar:1234/repo'}]},
            True,
        ),
        (
            {'repositories': ['sftp://foo@bar:1234/repo']},
            {'repositories': [{'path': 'sftp://foo@bar:1234/repo'}]},
            True,
        ),
        (
            {'repositories': ['rclone:host:repo']},
            {'repositories': [{'path': 'rclone:host:repo'}]},
            True,
        ),
        (
            {'repositories': ['s3:stuff']},
            {'repositories': [{'path': 's3:stuff'}]},
            True,
        ),
        (
            {'repositories': ['b2:stuff']},
            {'repositories': [{'path': 'b2:stuff'}]},
            True,
        ),
        (
            {'repositories': ['file:///repo']},
            {'repositories': [{'path': '/repo'}]},
            True,
        ),
        (
            {'repositories': [{'path': 'first'}, 'file:///repo']},
            {'repositories': [{'path': 'first'}, {'path': '/repo'}]},
            True,
        ),
        (
            {'repositories': [{'path': 'foo@bar:/repo', 'label': 'foo'}]},
            {'repositories': [{'path': 'ssh://foo@bar/repo', 'label': 'foo'}]},
            True,
        ),
        (
            {'repositories': [{'path': 'file:///repo', 'label': 'foo'}]},
            {'repositories': [{'path': '/repo', 'label': 'foo'}]},
            False,
        ),
        (
            {'repositories': [{'path': '/repo', 'label': 'foo'}]},
            {'repositories': [{'path': '/repo', 'label': 'foo'}]},
            False,
        ),
        (
            {'repositories': [{'path': None, 'label': 'foo'}]},
            {'repositories': []},
            False,
        ),
        (
            {'prefix': 'foo'},
            {'prefix': 'foo'},
            True,
        ),
    ),
)
def test_normalize_applies_hard_coded_normalization_to_config(
    config, expected_config, produces_logs
):
    flexmock(module).should_receive('normalize_sections').and_return([])
    flexmock(module).should_receive('normalize_commands').and_return([])

    logs = module.normalize('test.yaml', config)
    expected_config.setdefault('bootstrap', {})

    assert config == expected_config

    if produces_logs:
        assert logs
    else:
        assert logs == []


def test_normalize_config_with_borgmatic_source_directory_warns():
    flexmock(module).should_receive('normalize_sections').and_return([])
    flexmock(module).should_receive('normalize_commands').and_return([])

    logs = module.normalize('test.yaml', {'borgmatic_source_directory': '~/.borgmatic'})

    assert len(logs) == 1
    assert logs[0].levelno == module.logging.WARNING
    assert 'borgmatic_source_directory' in logs[0].msg
