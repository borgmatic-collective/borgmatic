import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import parse as module


def test_hash_adapter_is_always_equal():
    assert module.Hash_adapter({1: 2}) == module.Hash_adapter({3: 4})


def test_hash_adapter_alwaysh_hashes_the_same():
    assert hash(module.Hash_adapter({1: 2})) == hash(module.Hash_adapter({3: 4}))


def test_cache_ignoring_unhashable_arguments_caches_arguments_after_first_call():
    hashable = 3
    unhashable = {1, 2}
    calls = 0

    @module.cache_ignoring_unhashable_arguments
    def function(first, second, third):
        nonlocal calls
        calls += 1

        assert first == hashable
        assert second == unhashable
        assert third == unhashable

        return first

    assert function(hashable, unhashable, third=unhashable) == hashable
    assert calls == 1

    assert function(hashable, unhashable, third=unhashable) == hashable
    assert calls == 1


def test_resolve_credential_passes_through_string_without_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credential('{no credentials here}', config={}) == '{no credentials here}'


def test_resolve_credential_passes_through_none():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credential(None, config={}) is None


@pytest.mark.parametrize('invalid_value', ('{credential}', '{credential }', '{credential systemd}'))
def test_resolve_credential_with_invalid_credential_raises(invalid_value):
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    with pytest.raises(ValueError):
        module.resolve_credential(invalid_value, config={})


def test_resolve_credential_with_valid_credential_loads_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        ('mycredential',),
    ).and_return('result').once()

    assert module.resolve_credential('{credential systemd mycredential}', config={}) == 'result'


def test_resolve_credential_with_valid_credential_and_quoted_parameters_loads_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        ('my credential',),
    ).and_return('result').once()

    assert module.resolve_credential('{credential systemd "my credential"}', config={}) == 'result'


def test_resolve_credential_caches_credential_after_first_call():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        ('mycredential',),
    ).and_return('result').once()

    assert module.resolve_credential('{credential systemd mycredential}', config={}) == 'result'
    assert module.resolve_credential('{credential systemd mycredential}', config={}) == 'result'
