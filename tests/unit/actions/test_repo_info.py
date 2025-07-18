from flexmock import flexmock

from borgmatic.actions import repo_info as module


def test_run_repo_info_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.repo_info).should_receive('display_repository_info')
    repo_info_arguments = flexmock(repository=flexmock(), json=False)

    list(
        module.run_repo_info(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            repo_info_arguments=repo_info_arguments,
            global_arguments=flexmock(log_json=False),
            local_path=None,
            remote_path=None,
        ),
    )


def test_run_repo_info_parses_json():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.repo_info).should_receive('display_repository_info').and_return(
        flexmock(),
    )
    parsed_json = flexmock()
    flexmock(module.borgmatic.actions.json).should_receive('parse_json').and_return(parsed_json)
    repo_info_arguments = flexmock(repository=flexmock(), json=True)

    assert list(
        module.run_repo_info(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            repo_info_arguments=repo_info_arguments,
            global_arguments=flexmock(log_json=False),
            local_path=None,
            remote_path=None,
        ),
    ) == [parsed_json]
