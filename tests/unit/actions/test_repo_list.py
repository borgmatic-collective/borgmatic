from flexmock import flexmock

from borgmatic.actions import repo_list as module


def test_run_repo_list_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_list).should_receive('list_repository')
    repo_list_arguments = flexmock(repository=flexmock(), json=False)

    list(
        module.run_repo_list(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            repo_list_arguments=repo_list_arguments,
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        ),
    )


def test_run_repo_list_produces_json():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_list).should_receive('list_repository').and_return(
        flexmock(),
    )
    parsed_json = flexmock()
    flexmock(module.borgmatic.actions.json).should_receive('parse_json').and_return(parsed_json)
    repo_list_arguments = flexmock(repository=flexmock(), json=True)

    assert list(
        module.run_repo_list(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            repo_list_arguments=repo_list_arguments,
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        ),
    ) == [parsed_json]
