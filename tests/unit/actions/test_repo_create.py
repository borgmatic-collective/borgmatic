import pytest
from flexmock import flexmock

from borgmatic.actions import repo_create as module


def test_run_repo_create_with_encryption_mode_argument_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository')
    arguments = flexmock(
        encryption_mode=flexmock(),
        id_hash=flexmock(),
        key_location=flexmock(),
        source_repository=flexmock(),
        from_borg1=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=flexmock(),
        storage_quota=flexmock(),
        make_parent_directories=flexmock(),
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


def test_run_repo_create_with_encryption_mode_option_does_not_raise():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository')
    arguments = flexmock(
        encryption_mode=None,
        id_hash=flexmock(),
        key_location=flexmock(),
        source_repository=flexmock(),
        from_borg1=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=flexmock(),
        storage_quota=flexmock(),
        make_parent_directories=flexmock(),
    )

    module.run_repo_create(
        repository={'path': 'repo', 'encryption': flexmock()},
        config={},
        local_borg_version=None,
        repo_create_arguments=arguments,
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
    )


def test_run_repo_create_without_encryption_mode_raises():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository')
    arguments = flexmock(
        encryption_mode=None,
        id_hash=flexmock(),
        key_location=flexmock(),
        source_repository=flexmock(),
        from_borg1=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=flexmock(),
        storage_quota=flexmock(),
        make_parent_directories=flexmock(),
    )

    with pytest.raises(ValueError):
        module.run_repo_create(
            repository={'path': 'repo'},
            config={},
            local_borg_version=None,
            repo_create_arguments=arguments,
            global_arguments=flexmock(dry_run=False),
            local_path=None,
            remote_path=None,
        )


def test_run_repo_create_favors_flags_over_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository').with_args(
        dry_run=object,
        repository_path=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        encryption_mode=object,
        id_hash='blake17',
        key_location='repokey',
        source_repository=object,
        from_borg1=object,
        copy_crypt_key=object,
        append_only=False,
        storage_quota=0,
        make_parent_directories=False,
        local_path=object,
        remote_path=object,
    ).once()
    arguments = flexmock(
        encryption_mode=flexmock(),
        id_hash='blake17',
        key_location='repokey',
        source_repository=flexmock(),
        from_borg1=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=False,
        storage_quota=0,
        make_parent_directories=False,
    )

    module.run_repo_create(
        repository={
            'path': 'repo',
            'append_only': True,
            'storage_quota': '10G',
            'make_parent_directories': True,
            'id_hash': 'blake3',
            'key_location': 'keyfile',
        },
        config={},
        local_borg_version=None,
        repo_create_arguments=arguments,
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
    )


def test_run_repo_create_defaults_to_config():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.repo_create).should_receive('create_repository').with_args(
        dry_run=object,
        repository_path=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        encryption_mode=object,
        id_hash='blake3',
        key_location='keyfile',
        source_repository=object,
        from_borg1=object,
        copy_crypt_key=object,
        append_only=True,
        storage_quota='10G',
        make_parent_directories=True,
        local_path=object,
        remote_path=object,
    ).once()
    arguments = flexmock(
        encryption_mode=flexmock(),
        id_hash=None,
        key_location=None,
        source_repository=flexmock(),
        from_borg1=flexmock(),
        repository=flexmock(),
        copy_crypt_key=flexmock(),
        append_only=None,
        storage_quota=None,
        make_parent_directories=None,
    )

    module.run_repo_create(
        repository={
            'path': 'repo',
            'append_only': True,
            'storage_quota': '10G',
            'make_parent_directories': True,
            'id_hash': 'blake3',
            'key_location': 'keyfile',
        },
        config={},
        local_borg_version=None,
        repo_create_arguments=arguments,
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
    )
