import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import tag as module


def test_resolve_credential_passes_through_string_without_credential_tag():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credential('!no credentials here') == '!no credentials here'


def test_resolve_credential_passes_through_none():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credential(None) is None


def test_resolve_credential_with_invalid_credential_tag_raises():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    with pytest.raises(ValueError):
        module.resolve_credential('!credential systemd')


def test_resolve_credential_with_valid_credential_tag_loads_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        'mycredential',
    ).and_return('result').once()

    assert module.resolve_credential('!credential systemd mycredential') == 'result'


def test_resolve_credential_caches_credential_after_first_call():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        'mycredential',
    ).and_return('result').once()

    assert module.resolve_credential('!credential systemd mycredential') == 'result'
    assert module.resolve_credential('!credential systemd mycredential') == 'result'
