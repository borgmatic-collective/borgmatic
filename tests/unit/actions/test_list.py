from flexmock import flexmock

from borgmatic.actions import list as module


def test_run_list_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.list).should_receive('list_archive')
    list_arguments = flexmock(repository=flexmock(), archive=flexmock(), json=flexmock())

    list(
        module.run_list(
            repository='repo',
            storage={},
            local_borg_version=None,
            list_arguments=list_arguments,
            local_path=None,
            remote_path=None,
        )
    )
