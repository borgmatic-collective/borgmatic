from flexmock import flexmock

from borgmatic.actions import delete as module


def test_run_delete_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name')
    flexmock(module.borgmatic.actions.arguments).should_receive('update_arguments').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.delete).should_receive('delete_archives')

    module.run_delete(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        delete_arguments=flexmock(repository=flexmock(), archive=flexmock()),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )


def test_run_delete_without_archive_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name')
    flexmock(module.borgmatic.actions.arguments).should_receive('update_arguments').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.delete).should_receive('delete_archives')

    module.run_delete(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        delete_arguments=flexmock(repository=flexmock(), archive=None),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
