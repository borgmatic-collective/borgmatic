from flexmock import flexmock

from borgmatic.actions import rlist as module


def test_run_rlist_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.rlist).should_receive('list_repository')
    rlist_arguments = flexmock(repository=flexmock(), json=flexmock())

    list(
        module.run_rlist(
            repository='repo',
            storage={},
            local_borg_version=None,
            rlist_arguments=rlist_arguments,
            local_path=None,
            remote_path=None,
        )
    )
