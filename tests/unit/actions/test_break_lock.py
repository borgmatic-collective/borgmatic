from flexmock import flexmock

from borgmatic.actions import break_lock as module


def test_run_break_lock_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.break_lock).should_receive('break_lock')
    break_lock_arguments = flexmock(repository=flexmock())

    module.run_break_lock(
        repository='repo',
        storage={},
        local_borg_version=None,
        break_lock_arguments=break_lock_arguments,
        local_path=None,
        remote_path=None,
    )
