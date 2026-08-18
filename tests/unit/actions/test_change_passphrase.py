from flexmock import flexmock

from borgmatic.actions import change_passphrase as module


def test_run_change_passphrase_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.change_passphrase).should_receive('change_passphrase')
    change_passphrase_arguments = flexmock(repository=flexmock())

    module.run_change_passphrase(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        change_passphrase_arguments=change_passphrase_arguments,
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
