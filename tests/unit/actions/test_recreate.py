import pytest
from flexmock import flexmock

from borgmatic.actions import recreate as module


def test_run_recreate_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        None,
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
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive',
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
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive.recreate',
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
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive.recreate',
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


def test_run_recreate_with_archive_already_exists_error_raises():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive',
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive').and_raise(
        module.subprocess.CalledProcessError(
            returncode=module.BORG_EXIT_CODE_ARCHIVE_ALREADY_EXISTS,
            cmd='borg recreate or whatever',
        ),
    )

    with pytest.raises(ValueError):
        module.run_recreate(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            recreate_arguments=flexmock(repository=flexmock(), archive='test-archive', target=None),
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )


def test_run_recreate_with_target_and_archive_already_exists_error_raises():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive',
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive').and_raise(
        module.subprocess.CalledProcessError(
            returncode=module.BORG_EXIT_CODE_ARCHIVE_ALREADY_EXISTS,
            cmd='borg recreate or whatever',
        ),
    )

    with pytest.raises(ValueError):
        module.run_recreate(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            recreate_arguments=flexmock(
                repository=flexmock(),
                archive='test-archive',
                target='target-archive',
            ),
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )


def test_run_recreate_with_other_called_process_error_passes_it_through():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'test-archive',
    )
    flexmock(module.borgmatic.borg.recreate).should_receive('recreate_archive').and_raise(
        module.subprocess.CalledProcessError(
            returncode=1,
            cmd='borg recreate or whatever',
        ),
    )

    with pytest.raises(module.subprocess.CalledProcessError):
        module.run_recreate(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            recreate_arguments=flexmock(
                repository=flexmock(),
                archive='test-archive',
                target='target-archive',
            ),
            global_arguments=flexmock(),
            local_path=None,
            remote_path=None,
        )
