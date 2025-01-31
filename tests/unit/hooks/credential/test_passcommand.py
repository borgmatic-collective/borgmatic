import pytest
from flexmock import flexmock

from borgmatic.hooks.credential import passcommand as module


def test_run_passcommand_with_passphrase_configured_bails():
    flexmock(module.borgmatic.execute).should_receive('execute_command_and_capture_output').never()

    assert (
        module.run_passcommand('passcommand', passphrase_configured=True, working_directory=None)
        is None
    )


def test_run_passcommand_without_passphrase_configured_executes_passcommand():
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('passphrase').once()

    assert (
        module.run_passcommand('passcommand', passphrase_configured=False, working_directory=None)
        == 'passphrase'
    )


def test_load_credential_with_unknown_credential_name_errors():
    with pytest.raises(ValueError):
        module.load_credential(hook_config={}, config={}, credential_name='wtf')


def test_load_credential_with_configured_passcommand_runs_it():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('run_passcommand').with_args(
        'command', False, '/working'
    ).and_return('passphrase').once()

    assert (
        module.load_credential(
            hook_config={},
            config={'encryption_passcommand': 'command'},
            credential_name='encryption_passphrase',
        )
        == 'passphrase'
    )


def test_load_credential_with_configured_passphrase_and_passcommand_detects_passphrase():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('run_passcommand').with_args(
        'command', True, '/working'
    ).and_return(None).once()

    assert (
        module.load_credential(
            hook_config={},
            config={'encryption_passphrase': 'passphrase', 'encryption_passcommand': 'command'},
            credential_name='encryption_passphrase',
        )
        is None
    )
