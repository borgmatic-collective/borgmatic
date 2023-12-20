from flexmock import flexmock

from borgmatic.actions import rlist as module


def test_run_rlist_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.rlist).should_receive('list_repository')
    rlist_arguments = flexmock(repository=flexmock(), json=False)

    list(
        module.run_rlist(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            rlist_arguments=rlist_arguments,
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )
    )


def test_run_rlist_produces_json():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.rlist).should_receive('list_repository').and_return(flexmock())
    parsed_json = flexmock()
    flexmock(module.borgmatic.actions.json).should_receive('parse_json').and_return(parsed_json)
    rlist_arguments = flexmock(repository=flexmock(), json=True)

    assert list(
        module.run_rlist(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            rlist_arguments=rlist_arguments,
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )
    ) == [parsed_json]
