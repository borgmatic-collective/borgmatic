import io
import sys

from flexmock import flexmock
import pytest

from borgmatic.hooks.credential import systemd as module


def test_load_credential_without_credentials_directory_raises():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        None
    )

    with pytest.raises(ValueError):
        module.load_credential(hook_config={}, config={}, credential_name='mycredential')


def test_load_credential_with_invalid_credential_name_raises():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        '/var'
    )

    with pytest.raises(ValueError):
        module.load_credential(hook_config={}, config={}, credential_name='../../my!@#$credential')


def test_load_credential_reads_named_credential_from_file():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        '/var'
    )
    credential_stream = io.StringIO('password')
    credential_stream.name = '/var/mycredential'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/var/mycredential').and_return(credential_stream)

    assert (
        module.load_credential(hook_config={}, config={}, credential_name='mycredential')
        == 'password'
    )


def test_load_credential_with_file_not_found_error_raises():
    flexmock(module.os.environ).should_receive('get').with_args('CREDENTIALS_DIRECTORY').and_return(
        '/var'
    )
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/var/mycredential').and_raise(FileNotFoundError)

    with pytest.raises(ValueError):
        module.load_credential(hook_config={}, config={}, credential_name='mycredential')
