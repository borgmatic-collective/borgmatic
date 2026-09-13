import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import onepassword as module


@pytest.mark.parametrize('credential_parameters', ((), ('foo', 'bar')))
def test_load_credential_with_invalid_credential_parameters_raises(credential_parameters):
    flexmock(module.borgmatic.execute).should_receive('execute_command_and_capture_output').never()

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=credential_parameters,
        )


def test_load_credential_with_invalid_secret_reference_raises():
    flexmock(module.borgmatic.execute).should_receive('execute_command_and_capture_output').never()

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('not-a-secret-reference',),
        )


def test_load_credential_fetches_secret_reference():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'op',
            'read',
            '--no-newline',
            'op://vault/item/field',
        ),
    ).and_yield('password').once()

    assert (
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('op://vault/item/field',),
        )
        == 'password'
    )


def test_load_credential_with_custom_op_command_calls_it():
    config = {'onepassword': {'op_command': '/usr/local/bin/op --account my.1password.com'}}
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            '/usr/local/bin/op',
            '--account',
            'my.1password.com',
            'read',
            '--no-newline',
            'op://vault/item/field',
        ),
    ).and_yield('password').once()

    assert (
        module.load_credential(
            hook_config=config['onepassword'],
            config=config,
            credential_parameters=('op://vault/item/field',),
        )
        == 'password'
    )


def test_load_credential_with_section_in_reference():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'op',
            'read',
            '--no-newline',
            'op://vault/item/section/field',
        ),
    ).and_yield('password').once()

    assert (
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('op://vault/item/section/field',),
        )
        == 'password'
    )
