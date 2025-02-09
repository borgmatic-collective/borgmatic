import pytest
from flexmock import flexmock

from borgmatic.config import credential as module


def test_resolve_credentials_passes_through_string_without_credential_tag():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert (
        module.resolve_credentials(config=flexmock(), item='!no credentials here')
        == '!no credentials here'
    )


def test_resolve_credentials_passes_through_none():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credentials(config=flexmock(), item=None) == None


def test_resolve_credentials_with_invalid_credential_tag_raises():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    with pytest.raises(ValueError):
        module.resolve_credentials(config=flexmock(), item='!credential systemd')


def test_resolve_credentials_with_valid_credential_tag_loads_credential():
    config = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'mycredential',
    ).and_return('result').once()

    assert (
        module.resolve_credentials(config=config, item='!credential systemd mycredential')
        == 'result'
    )


def test_resolve_credentials_with_list_recurses_and_loads_credentials():
    config = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'mycredential',
    ).and_return('result1').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'othercredential',
    ).and_return('result2').once()

    assert module.resolve_credentials(
        config=config,
        item=['!credential systemd mycredential', 'nope', '!credential systemd othercredential'],
    ) == ['result1', 'nope', 'result2']


def test_resolve_credentials_with_dict_recurses_and_loads_credentials():
    config = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'mycredential',
    ).and_return('result1').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'othercredential',
    ).and_return('result2').once()

    assert module.resolve_credentials(
        config=config,
        item={
            'a': '!credential systemd mycredential',
            'b': 'nope',
            'c': '!credential systemd othercredential',
        },
    ) == {'a': 'result1', 'b': 'nope', 'c': 'result2'}


def test_resolve_credentials_with_list_of_dicts_recurses_and_loads_credentials():
    config = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'mycredential',
    ).and_return('result1').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'othercredential',
    ).and_return('result2').once()

    assert module.resolve_credentials(
        config=config,
        item=[
            {'a': '!credential systemd mycredential', 'b': 'nope'},
            {'c': '!credential systemd othercredential'},
        ],
    ) == [{'a': 'result1', 'b': 'nope'}, {'c': 'result2'}]


def test_resolve_credentials_with_dict_of_lists_recurses_and_loads_credentials():
    config = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'mycredential',
    ).and_return('result1').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        config,
        'systemd',
        'othercredential',
    ).and_return('result2').once()

    assert module.resolve_credentials(
        config=config,
        item={
            'a': ['!credential systemd mycredential', 'nope'],
            'b': ['!credential systemd othercredential'],
        },
    ) == {'a': ['result1', 'nope'], 'b': ['result2']}
