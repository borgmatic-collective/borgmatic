from flexmock import flexmock

from borgmatic.borg import passcommand as module


def test_run_passcommand_with_passphrase_configured_bails():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.execute).should_receive('execute_command_and_capture_output').never()

    assert (
        module.run_passcommand('passcommand', passphrase_configured=True, working_directory=None)
        is None
    )


def test_run_passcommand_without_passphrase_configured_executes_passcommand():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('passphrase').once()

    assert (
        module.run_passcommand('passcommand', passphrase_configured=False, working_directory=None)
        == 'passphrase'
    )


def test_get_passphrase_from_passcommand_with_configured_passcommand_runs_it():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('run_passcommand').with_args(
        'command', False, '/working'
    ).and_return('passphrase').once()

    assert (
        module.get_passphrase_from_passcommand(
            {'encryption_passcommand': 'command'},
        )
        == 'passphrase'
    )


def test_get_passphrase_from_passcommand_with_configured_passphrase_and_passcommand_detects_passphrase():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('run_passcommand').with_args(
        'command', True, '/working'
    ).and_return(None).once()

    assert (
        module.get_passphrase_from_passcommand(
            {'encryption_passphrase': 'passphrase', 'encryption_passcommand': 'command'},
        )
        is None
    )


def test_get_passphrase_from_passcommand_with_configured_blank_passphrase_and_passcommand_detects_passphrase():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('run_passcommand').with_args(
        'command', True, '/working'
    ).and_return(None).once()

    assert (
        module.get_passphrase_from_passcommand(
            {'encryption_passphrase': '', 'encryption_passcommand': 'command'},
        )
        is None
    )


def test_run_passcommand_caches_passcommand_after_first_call():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return('passphrase').once()

    assert (
        module.run_passcommand('passcommand', passphrase_configured=False, working_directory=None)
        == 'passphrase'
    )
    assert (
        module.run_passcommand('passcommand', passphrase_configured=False, working_directory=None)
        == 'passphrase'
    )
