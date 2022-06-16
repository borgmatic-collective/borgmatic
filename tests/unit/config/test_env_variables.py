import pytest

from borgmatic.config import override as module


def test_env(monkeypatch):
    monkeypatch.setenv("MY_CUSTOM_VALUE", "foo")
    config = {'key': 'Hello $MY_CUSTOM_VALUE'}
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello $MY_CUSTOM_VALUE'}


def test_env_braces(monkeypatch):
    monkeypatch.setenv("MY_CUSTOM_VALUE", "foo")
    config = {'key': 'Hello ${MY_CUSTOM_VALUE}'}
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello foo'}


def test_env_default_value(monkeypatch):
    monkeypatch.delenv("MY_CUSTOM_VALUE", raising=False)
    config = {'key': 'Hello ${MY_CUSTOM_VALUE:-bar}'}
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello bar'}


def test_env_unknown(monkeypatch):
    monkeypatch.delenv("MY_CUSTOM_VALUE", raising=False)
    config = {'key': 'Hello ${MY_CUSTOM_VALUE}'}
    with pytest.raises(ValueError):
        module.resolve_env_variables(config)


def test_env_full(monkeypatch):
    monkeypatch.setenv("MY_CUSTOM_VALUE", "foo")
    monkeypatch.delenv("MY_CUSTOM_VALUE2", raising=False)
    config = {
        'key': 'Hello $MY_CUSTOM_VALUE is not resolved',
        'dict': {
            'key': 'value',
            'anotherdict': {
                'key': 'My ${MY_CUSTOM_VALUE} here',
                'other': '${MY_CUSTOM_VALUE}',
                'list': [
                    '/home/${MY_CUSTOM_VALUE}/.local',
                    '/var/log/',
                    '/home/${MY_CUSTOM_VALUE2:-bar}/.config',
                ],
            },
        },
        'list': [
            '/home/${MY_CUSTOM_VALUE}/.local',
            '/var/log/',
            '/home/${MY_CUSTOM_VALUE2-bar}/.config',
        ],
    }
    module.resolve_env_variables(config)
    assert config == {
        'key': 'Hello $MY_CUSTOM_VALUE is not resolved',
        'dict': {
            'key': 'value',
            'anotherdict': {
                'key': 'My foo here',
                'other': 'foo',
                'list': ['/home/foo/.local', '/var/log/', '/home/bar/.config',],
            },
        },
        'list': ['/home/foo/.local', '/var/log/', '/home/bar/.config',],
    }
