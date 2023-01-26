from flexmock import flexmock

from borgmatic.actions import transfer as module


def test_run_transfer_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.transfer).should_receive('transfer_archives')
    transfer_arguments = flexmock()
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_transfer(
        repository='repo',
        storage={},
        local_borg_version=None,
        transfer_arguments=transfer_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
