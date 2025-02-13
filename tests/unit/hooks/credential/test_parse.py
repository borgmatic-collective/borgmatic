import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import parse as module


def test_resolve_credential_passes_through_string_without_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credential('{no credentials here}') == '{no credentials here}'


def test_resolve_credential_passes_through_none():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    assert module.resolve_credential(None) is None


@pytest.mark.parametrize('invalid_value', ('{credential}', '{credential }', '{credential systemd}'))
def test_resolve_credential_with_invalid_credential_raises(invalid_value):
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').never()

    with pytest.raises(ValueError):
        module.resolve_credential(invalid_value)


def test_resolve_credential_with_valid_credential_loads_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        ('mycredential',),
    ).and_return('result').once()

    assert module.resolve_credential('{credential systemd mycredential}') == 'result'


def test_resolve_credential_with_valid_credential_and_quoted_parameters_loads_credential():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        ('my credential',),
    ).and_return('result').once()

    assert module.resolve_credential('{credential systemd "my credential"}') == 'result'


def test_resolve_credential_caches_credential_after_first_call():
    module.resolve_credential.cache_clear()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        'load_credential',
        {},
        'systemd',
        ('mycredential',),
    ).and_return('result').once()

    assert module.resolve_credential('{credential systemd mycredential}') == 'result'
    assert module.resolve_credential('{credential systemd mycredential}') == 'result'
