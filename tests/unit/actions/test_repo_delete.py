from flexmock import flexmock

from borgmatic.actions import repo_delete as module


def test_run_repo_delete_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.actions.arguments).should_receive('update_arguments').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository')

    module.run_repo_delete(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        repo_delete_arguments=flexmock(repository=flexmock(), cache_only=False),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )


def test_run_repo_delete_with_cache_only_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.actions.arguments).should_receive('update_arguments').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository')

    module.run_repo_delete(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        repo_delete_arguments=flexmock(repository=flexmock(), cache_only=True),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
