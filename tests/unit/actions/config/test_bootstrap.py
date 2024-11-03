import pytest
from flexmock import flexmock

from borgmatic.actions.config import bootstrap as module


def test_make_bootstrap_config_uses_ssh_command_argument():
    ssh_command = flexmock()

    config = module.make_bootstrap_config(flexmock(ssh_command=ssh_command))
    assert config['ssh_command'] == ssh_command
    assert config['relocated_repo_access_is_ok']


def test_get_config_paths_returns_list_of_config_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/source')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/runtime')
    flexmock(module).should_receive('make_bootstrap_config').and_return({})
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        ssh_command=None,
        local_path='borg7',
        remote_path='borg8',
        borgmatic_source_directory=None,
        user_runtime_directory=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["/borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    )

    assert module.get_config_paths(
        'archive', bootstrap_arguments, global_arguments, local_borg_version
    ) == ['/borgmatic/config.yaml']


def test_get_config_paths_translates_ssh_command_argument_to_config():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/source')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/runtime')
    config = flexmock()
    flexmock(module).should_receive('make_bootstrap_config').and_return(config)
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        ssh_command='ssh -i key',
        local_path='borg7',
        remote_path='borg8',
        borgmatic_source_directory=None,
        user_runtime_directory=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["/borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').with_args(
        False,
        'repo',
        'archive',
        object,
        config,
        object,
        object,
        extract_to_stdout=True,
        local_path='borg7',
        remote_path='borg8',
    ).and_return(extract_process)

    assert module.get_config_paths(
        'archive', bootstrap_arguments, global_arguments, local_borg_version
    ) == ['/borgmatic/config.yaml']


def test_get_config_paths_with_missing_manifest_raises_value_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/source')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/runtime')
    flexmock(module).should_receive('make_bootstrap_config').and_return({})
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        ssh_command=None,
        local_path='borg7',
        remote_path='borg7',
        borgmatic_source_directory=None,
        user_runtime_directory=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(stdout=flexmock(read=lambda: ''))
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    )

    with pytest.raises(ValueError):
        module.get_config_paths(
            'archive', bootstrap_arguments, global_arguments, local_borg_version
        )


def test_get_config_paths_with_broken_json_raises_value_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/source')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/runtime')
    flexmock(module).should_receive('make_bootstrap_config').and_return({})
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        ssh_command=None,
        local_path='borg7',
        remote_path='borg7',
        borgmatic_source_directory=None,
        user_runtime_directory=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(read=lambda: '{"config_paths": ["/oops'),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    )

    with pytest.raises(ValueError):
        module.get_config_paths(
            'archive', bootstrap_arguments, global_arguments, local_borg_version
        )


def test_get_config_paths_with_json_missing_key_raises_value_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/source')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/runtime')
    flexmock(module).should_receive('make_bootstrap_config').and_return({})
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        ssh_command=None,
        local_path='borg7',
        remote_path='borg7',
        borgmatic_source_directory=None,
        user_runtime_directory=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(read=lambda: '{}'),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    )

    with pytest.raises(ValueError):
        module.get_config_paths(
            'archive', bootstrap_arguments, global_arguments, local_borg_version
        )


def test_run_bootstrap_does_not_raise():
    flexmock(module).should_receive('make_bootstrap_config').and_return({})
    flexmock(module).should_receive('get_config_paths').and_return(['/borgmatic/config.yaml'])
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        destination='dest',
        strip_components=1,
        progress=False,
        user_runtime_directory='/borgmatic',
        ssh_command=None,
        local_path='borg7',
        remote_path='borg8',
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process
    ).once()
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    )

    module.run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version)


def test_run_bootstrap_translates_ssh_command_argument_to_config():
    config = flexmock()
    flexmock(module).should_receive('make_bootstrap_config').and_return(config)
    flexmock(module).should_receive('get_config_paths').and_return(['/borgmatic/config.yaml'])
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        destination='dest',
        strip_components=1,
        progress=False,
        user_runtime_directory='/borgmatic',
        ssh_command='ssh -i key',
        local_path='borg7',
        remote_path='borg8',
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').with_args(
        False,
        'repo',
        'archive',
        object,
        config,
        object,
        object,
        extract_to_stdout=False,
        destination_path='dest',
        strip_components=1,
        progress=False,
        local_path='borg7',
        remote_path='borg8',
    ).and_return(extract_process).once()
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').with_args(
        'repo',
        'archive',
        config,
        object,
        object,
        local_path='borg7',
        remote_path='borg8',
    ).and_return('archive')

    module.run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version)
