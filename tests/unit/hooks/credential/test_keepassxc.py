import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import keepassxc as module


@pytest.mark.parametrize('credential_parameters', ((), ('foo',), ('foo', 'bar', 'baz')))
def test_load_credential_with_invalid_credential_parameters_raises(credential_parameters):
    flexmock(module.borgmatic.execute).should_receive('execute_command_and_capture_output').never()

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=credential_parameters,
        )


def test_load_credential_with_missing_database_raises():
    flexmock(module.os.path).should_receive('expanduser').with_args('database.kdbx').and_return(
        'database.kdbx',
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.execute).should_receive('execute_command_and_capture_output').never()

    with pytest.raises(ValueError):
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('database.kdbx', 'mypassword'),
        )


def test_load_credential_with_present_database_fetches_password_from_keepassxc():
    flexmock(module.os.path).should_receive('expanduser').with_args('database.kdbx').and_return(
        'database.kdbx',
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'keepassxc-cli',
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            'database.kdbx',
            'mypassword',
        ),
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('database.kdbx', 'mypassword'),
        )
        == 'password'
    )


def test_load_credential_with_custom_keepassxc_cli_command_calls_it():
    flexmock(module.os.path).should_receive('expanduser').with_args('database.kdbx').and_return(
        'database.kdbx',
    )
    config = {'keepassxc': {'keepassxc_cli_command': '/usr/local/bin/keepassxc-cli --some-option'}}
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            '/usr/local/bin/keepassxc-cli',
            '--some-option',
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            'database.kdbx',
            'mypassword',
        ),
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config=config['keepassxc'],
            config=config,
            credential_parameters=('database.kdbx', 'mypassword'),
        )
        == 'password'
    )


def test_load_credential_with_expanded_directory_with_present_database_fetches_password_from_keepassxc():
    flexmock(module.os.path).should_receive('expanduser').with_args('~/database.kdbx').and_return(
        '/root/database.kdbx',
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'keepassxc-cli',
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            '/root/database.kdbx',
            'mypassword',
        ),
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config={},
            config={},
            credential_parameters=('~/database.kdbx', 'mypassword'),
        )
        == 'password'
    )


def test_load_credential_with_key_file():
    flexmock(module.os.path).should_receive('expanduser').with_args('database.kdbx').and_return(
        'database.kdbx',
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'keepassxc-cli',
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            '--key-file',
            '/path/to/keyfile',
            'database.kdbx',
            'mypassword',
        ),
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config={'key_file': '/path/to/keyfile'},
            config={},
            credential_parameters=('database.kdbx', 'mypassword'),
        )
        == 'password'
    )


def test_load_credential_with_yubikey():
    flexmock(module.os.path).should_receive('expanduser').with_args('database.kdbx').and_return(
        'database.kdbx',
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'keepassxc-cli',
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            '--yubikey',
            '1:7370001',
            'database.kdbx',
            'mypassword',
        ),
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config={'yubikey': '1:7370001'},
            config={},
            credential_parameters=('database.kdbx', 'mypassword'),
        )
        == 'password'
    )


def test_load_credential_with_key_file_and_yubikey():
    flexmock(module.os.path).should_receive('expanduser').with_args('database.kdbx').and_return(
        'database.kdbx',
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        (
            'keepassxc-cli',
            'show',
            '--show-protected',
            '--attributes',
            'Password',
            '--key-file',
            '/path/to/keyfile',
            '--yubikey',
            '2',
            'database.kdbx',
            'mypassword',
        ),
    ).and_return('password').once()

    assert (
        module.load_credential(
            hook_config={'key_file': '/path/to/keyfile', 'yubikey': '2'},
            config={},
            credential_parameters=('database.kdbx', 'mypassword'),
        )
        == 'password'
    )
