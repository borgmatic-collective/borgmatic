from flexmock import flexmock

from borgmatic.actions import rinfo as module


def test_run_rinfo_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.rinfo).should_receive('display_repository_info')
    rinfo_arguments = flexmock(repository=flexmock(), json=flexmock())

    list(
        module.run_rinfo(
            repository='repo',
            storage={},
            local_borg_version=None,
            rinfo_arguments=rinfo_arguments,
            local_path=None,
            remote_path=None,
        )
    )
