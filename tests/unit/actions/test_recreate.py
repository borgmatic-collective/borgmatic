import pytest
from flexmock import flexmock

from borgmatic.actions import recreate as module


def test_run_recreate_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        None
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive')

    module.run_recreate(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        recreate_arguments=flexmock(repository=flexmock(), archive=None),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )


def test_run_recreate_with_archive_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive'
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive')

    module.run_recreate(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        recreate_arguments=flexmock(repository=flexmock(), archive='test-archive'),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )


def test_run_recreate_with_leftover_recreate_archive_raises():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive.recreate'
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive')

    with pytest.raises(ValueError):
        module.run_recreate(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            recreate_arguments=flexmock(repository=flexmock(), archive='test-archive.recreate'),
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )


def test_run_recreate_with_latest_archive_resolving_to_leftover_recreate_archive_raises():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive.recreate'
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive')

    with pytest.raises(ValueError):
        module.run_recreate(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            recreate_arguments=flexmock(repository=flexmock(), archive='latest'),
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )
