import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import file as module


@pytest.mark.parametrize('credential_parameters', ((), ('foo', 'bar')))
def test_load_credential_with_invalid_credential_parameters_raises(credential_parameters):
    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={}, config={}, credential_parameters=credential_parameters
        )


def test_load_credential_with_invalid_credential_name_raises():
    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={}, config={}, credential_parameters=('this is invalid',)
        )


def test_load_credential_reads_named_credential_from_file():
    credential_stream = io.StringIO('password')
    credential_stream.name = '/credentials/mycredential'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/credentials/mycredential').and_return(
        credential_stream
    )

    assert (
        module.load_credential(
            hook_config={}, config={}, credential_parameters=('/credentials/mycredential',)
        )
        == 'password'
    )


def test_load_credential_reads_named_credential_from_file_using_working_directory():
    credential_stream = io.StringIO('password')
    credential_stream.name = '/working/credentials/mycredential'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/working/credentials/mycredential').and_return(
        credential_stream
    )

    assert (
        module.load_credential(
            hook_config={},
            config={'working_directory': '/working'},
            credential_parameters=('credentials/mycredential',),
        )
        == 'password'
    )


def test_load_credential_with_file_not_found_error_raises():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/credentials/mycredential').and_raise(
        FileNotFoundError
    )

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={}, config={}, credential_parameters=('/credentials/mycredential',)
        )
