import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import systemd as module


@pytest.mark.parametrize('credential_parameters', ((), ('foo', 'bar')))
def test_load_credential_with_invalid_credential_parameters_raises(credential_parameters):
    flexmock(module.os.environ).should_receive('get').never()

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=credential_parameters,
        )


def test_load_credential_without_credentials_directory_falls_back_to_systemd_creds_command():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        None,
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('systemd-creds', 'decrypt', '/etc/credstore.encrypted/mycredential')).and_return(
        'password'
    ).once()

    assert (
        module.load_credential(hook_config={}, config={}, credential_parameters=('mycredential',))
        == 'password'
    )


def test_load_credential_without_credentials_directory_calls_custom_systemd_creds_command():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        None,
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(
        ('/path/to/systemd-creds', '--flag', 'decrypt', '/etc/credstore.encrypted/mycredential')
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config={'systemd_creds_command': '/path/to/systemd-creds --flag'},
            config={},
            credential_parameters=('mycredential',),
        )
        == 'password'
    )


def test_load_credential_without_credentials_directory_uses_custom_encrypted_credentials_directory():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        None,
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('systemd-creds', 'decrypt', '/my/credstore.encrypted/mycredential')).and_return(
        'password'
    ).once()

    assert (
        module.load_credential(
            hook_config={'encrypted_credentials_directory': '/my/credstore.encrypted'},
            config={},
            credential_parameters=('mycredential',),
        )
        == 'password'
    )


def test_load_credential_with_invalid_credential_name_raises():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        '/var',
    )

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('../../my!@#$credential',),
        )


def test_load_credential_reads_named_credential_from_file():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        '/var',
    )
    credential_stream = io.StringIO('password')
    credential_stream.name = '/var/borgmatic.pw'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/var/borgmatic.pw', encoding='utf-8').and_return(
        credential_stream
    )

    assert (
        module.load_credential(hook_config={}, config={}, credential_parameters=('borgmatic.pw',))
        == 'password'
    )


def test_load_credential_with_file_not_found_error_raises():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        '/var',
    )
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/var/mycredential', encoding='utf-8').and_raise(
        FileNotFoundError
    )

    with pytest.raises(ValueError):
        module.load_credential(hook_config={}, config={}, credential_parameters=('mycredential',))
