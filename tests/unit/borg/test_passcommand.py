from flexmock import flexmock

from borgmatic.borg import passcommand as module


def test_run_passcommand_does_not_raise():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('passphrase')

    assert module.run_passcommand('passcommand', working_directory=None) == 'passphrase'


def test_get_passphrase_from_passcommand_with_configured_passcommand_runs_it():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working',
    )
    flexmock(module).should_receive('run_passcommand').with_args('command', '/working').and_return(
        'passphrase',
    ).once()

    assert (
        module.get_passphrase_from_passcommand(
            {'encryption_passcommand': 'command'},
        )
        == 'passphrase'
    )


def test_get_passphrase_from_passcommand_without_configured_passcommand_bails():
    flexmock(module).should_receive('run_passcommand').never()

    assert module.get_passphrase_from_passcommand({}) is None


def test_run_passcommand_caches_passcommand_after_first_call():
    module.run_passcommand.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('passphrase').once()

    assert module.run_passcommand('passcommand', working_directory=None) == 'passphrase'
    assert module.run_passcommand('passcommand', working_directory=None) == 'passphrase'
