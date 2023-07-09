from flexmock import flexmock

from borgmatic.actions import info as module


def test_run_info_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.arguments).should_receive('update_arguments').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.info).should_receive('display_archives_info')
    info_arguments = flexmock(repository=flexmock(), archive=flexmock(), json=flexmock())

    list(
        module.run_info(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            info_arguments=info_arguments,
            global_arguments=flexmock(log_json=False),
            local_path=None,
            remote_path=None,
        )
    )
