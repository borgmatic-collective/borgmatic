import pytest

from borgmatic.config import environment as module


def test_env(monkeypatch):
    monkeypatch.setenv('MY_CUSTOM_VALUE', 'foo')
    config = {'key': 'Hello $MY_CUSTOM_VALUE'}
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello $MY_CUSTOM_VALUE'}


def test_env_braces(monkeypatch):
    monkeypatch.setenv('MY_CUSTOM_VALUE', 'foo')
    config = {'key': 'Hello ${MY_CUSTOM_VALUE}'}  # noqa: FS003
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello foo'}


def test_env_multi(monkeypatch):
    monkeypatch.setenv('MY_CUSTOM_VALUE', 'foo')
    monkeypatch.setenv('MY_CUSTOM_VALUE2', 'bar')
    config = {'key': 'Hello ${MY_CUSTOM_VALUE}${MY_CUSTOM_VALUE2}'}  # noqa: FS003
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello foobar'}


def test_env_escape(monkeypatch):
    monkeypatch.setenv('MY_CUSTOM_VALUE', 'foo')
    monkeypatch.setenv('MY_CUSTOM_VALUE2', 'bar')
    config = {'key': r'Hello ${MY_CUSTOM_VALUE} \${MY_CUSTOM_VALUE}'}  # noqa: FS003
    module.resolve_env_variables(config)
    assert config == {'key': r'Hello foo ${MY_CUSTOM_VALUE}'}  # noqa: FS003


def test_env_default_value(monkeypatch):
    monkeypatch.delenv('MY_CUSTOM_VALUE', raising=False)
    config = {'key': 'Hello ${MY_CUSTOM_VALUE:-bar}'}  # noqa: FS003
    module.resolve_env_variables(config)
    assert config == {'key': 'Hello bar'}


def test_env_unknown(monkeypatch):
    monkeypatch.delenv('MY_CUSTOM_VALUE', raising=False)
    config = {'key': 'Hello ${MY_CUSTOM_VALUE}'}  # noqa: FS003
    with pytest.raises(ValueError):
        module.resolve_env_variables(config)


def test_env_full(monkeypatch):
    monkeypatch.setenv('MY_CUSTOM_VALUE', 'foo')
    monkeypatch.delenv('MY_CUSTOM_VALUE2', raising=False)
    config = {
        'key': 'Hello $MY_CUSTOM_VALUE is not resolved',
        'dict': {
            'key': 'value',
            'anotherdict': {
                'key': 'My ${MY_CUSTOM_VALUE} here',  # noqa: FS003
                'other': '${MY_CUSTOM_VALUE}',  # noqa: FS003
                'escaped': r'\${MY_CUSTOM_VALUE}',  # noqa: FS003
                'list': [
                    '/home/${MY_CUSTOM_VALUE}/.local',  # noqa: FS003
                    '/var/log/',
                    '/home/${MY_CUSTOM_VALUE2:-bar}/.config',  # noqa: FS003
                ],
            },
        },
        'list': [
            '/home/${MY_CUSTOM_VALUE}/.local',  # noqa: FS003
            '/var/log/',
            '/home/${MY_CUSTOM_VALUE2-bar}/.config',  # noqa: FS003
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
                'escaped': '${MY_CUSTOM_VALUE}',  # noqa: FS003
                'list': ['/home/foo/.local', '/var/log/', '/home/bar/.config'],
            },
        },
        'list': ['/home/foo/.local', '/var/log/', '/home/bar/.config'],
    }
