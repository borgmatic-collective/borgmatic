from flexmock import flexmock

from borgmatic.actions import repo_create as module


def test_run_repo_create_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository')
    arguments = flexmock(
        encryption_mode=flexmock(),
        source_repository=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=flexmock(),
        storage_quota=flexmock(),
        make_parent_dirs=flexmock(),
    )

    module.run_repo_create(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        repo_create_arguments=arguments,
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
    )


def test_run_repo_create_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(
        False
    )
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository').never()
    arguments = flexmock(
        encryption_mode=flexmock(),
        source_repository=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=flexmock(),
        storage_quota=flexmock(),
        make_parent_dirs=flexmock(),
    )

    module.run_repo_create(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        repo_create_arguments=arguments,
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
    )
