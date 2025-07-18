import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import container as module


@pytest.mark.parametrize('credential_parameters', ((), ('foo', 'bar')))
def test_load_credential_with_invalid_credential_parameters_raises(credential_parameters):
    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=credential_parameters,
        )


def test_load_credential_with_invalid_secret_name_raises():
    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('this is invalid',),
        )


def test_load_credential_reads_named_secret_from_file():
    credential_stream = io.StringIO('password')
    credential_stream.name = '/run/secrets/mysecret'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/run/secrets/mysecret', encoding='utf-8').and_return(
        credential_stream
    )

    assert (
        module.load_credential(hook_config={}, config={}, credential_parameters=('mysecret',))
        == 'password'
    )


def test_load_credential_with_custom_secrets_directory_looks_there_for_secret_file():
    config = {'container': {'secrets_directory': '/secrets'}}
    credential_stream = io.StringIO('password')
    credential_stream.name = '/secrets/mysecret'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/secrets/mysecret', encoding='utf-8').and_return(
        credential_stream
    )

    assert (
        module.load_credential(
            hook_config=config['container'],
            config=config,
            credential_parameters=('mysecret',),
        )
        == 'password'
    )


def test_load_credential_with_custom_secrets_directory_prefixes_it_with_working_directory():
    config = {'container': {'secrets_directory': 'secrets'}, 'working_directory': '/working'}
    credential_stream = io.StringIO('password')
    credential_stream.name = '/working/secrets/mysecret'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(
        '/working/secrets/mysecret', encoding='utf-8'
    ).and_return(
        credential_stream,
    )

    assert (
        module.load_credential(
            hook_config=config['container'],
            config=config,
            credential_parameters=('mysecret',),
        )
        == 'password'
    )


def test_load_credential_with_file_not_found_error_raises():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('/run/secrets/mysecret', encoding='utf-8').and_raise(
        FileNotFoundError
    )

    with pytest.raises(ValueError):
        module.load_credential(hook_config={}, config={}, credential_parameters=('mysecret',))
