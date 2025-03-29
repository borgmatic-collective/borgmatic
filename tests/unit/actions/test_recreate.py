from flexmock import flexmock

from borgmatic.actions import recreate as module


def test_run_recreate_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive')

    recreate_arguments = flexmock(repository=flexmock(), archive=None)

    module.run_recreate(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        recreate_arguments=recreate_arguments,
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )


def test_run_recreate_with_archive_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive')

    recreate_arguments = flexmock(repository=flexmock(), archive='test-archive')

    module.run_recreate(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        recreate_arguments=recreate_arguments,
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
