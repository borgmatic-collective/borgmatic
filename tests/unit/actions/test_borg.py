from flexmock import flexmock

from borgmatic.actions import borg as module


def test_run_borg_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.borg).should_receive('run_arbitrary_borg')
    borg_arguments = flexmock(repository=flexmock(), archive=flexmock(), options=flexmock())

    module.run_borg(
        repository={'path': 'repos'},
        config={},
        local_borg_version=None,
        global_arguments=flexmock(log_json=False),
        borg_arguments=borg_arguments,
        local_path=None,
        remote_path=None,
    )
