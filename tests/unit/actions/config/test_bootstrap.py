import pytest
from flexmock import flexmock

from borgmatic.actions.config import bootstrap as module


def test_make_bootstrap_config_uses_bootstrap_arguments():
    config = module.make_bootstrap_config(
        flexmock(
            borgmatic_source_directory='/source',
            local_path='borg1',
            remote_path='borg2',
            ssh_command='ssh',
            user_runtime_directory='/run',
        )
    )

    assert config['borgmatic_source_directory'] == '/source'
    assert config['local_path'] == 'borg1'
    assert config['remote_path'] == 'borg2'
    assert config['relocated_repo_access_is_ok']
    assert config['ssh_command'] == 'ssh'
    assert config['user_runtime_directory'] == '/run'


def test_load_config_paths_from_archive_returns_list_of_config_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/source')
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["/borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process,
    )

    assert module.load_config_paths_from_archive(
        'repo',
        'archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(dry_run=False),
        borgmatic_runtime_directory='/run',
    ) == ['/borgmatic/config.yaml']


def test_load_config_paths_from_archive_probes_for_manifest():
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/source')
    flexmock(module.os.path).should_call('join').with_args(
        'borgmatic',
        'bootstrap',
        'manifest.json',
    ).once()
    flexmock(module.os.path).should_call('join').with_args(
        '/run',
        'bootstrap',
        'manifest.json',
    ).once()
    flexmock(module.os.path).should_call('join').with_args(
        '/source',
        'bootstrap',
        'manifest.json',
    ).once()
    manifest_missing_extract_process = flexmock(
        stdout=flexmock(read=lambda: None),
    )
    manifest_found_extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["/borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        manifest_missing_extract_process,
    ).and_return(manifest_missing_extract_process).and_return(manifest_found_extract_process)

    assert module.load_config_paths_from_archive(
        'repo',
        'archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(dry_run=False),
        borgmatic_runtime_directory='/run',
    ) == ['/borgmatic/config.yaml']


def test_load_config_paths_from_archive_with_missing_manifest_raises_value_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/source')
    extract_process = flexmock(stdout=flexmock(read=lambda: ''))
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process,
    )

    with pytest.raises(ValueError):
        module.load_config_paths_from_archive(
            'repo',
            'archive',
            config={},
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=False),
            borgmatic_runtime_directory='/run',
        )


def test_load_config_paths_from_archive_with_broken_json_raises_value_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/source')
    extract_process = flexmock(
        stdout=flexmock(read=lambda: '{"config_paths": ["/oops'),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process,
    )

    with pytest.raises(ValueError):
        module.load_config_paths_from_archive(
            'repo',
            'archive',
            config={},
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=False),
            borgmatic_runtime_directory='/run',
        )


def test_load_config_paths_from_archive_with_json_missing_key_raises_value_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/source')
    extract_process = flexmock(
        stdout=flexmock(read=lambda: '{}'),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process,
    )

    with pytest.raises(ValueError):
        module.load_config_paths_from_archive(
            'repo',
            'archive',
            config={},
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=False),
            borgmatic_runtime_directory='/run',
        )


def test_run_bootstrap_does_not_raise():
    flexmock(module).should_receive('make_bootstrap_config').and_return({})
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive',
    )
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock(),
    )
    flexmock(module).should_receive('load_config_paths_from_archive').and_return(
        ['/borgmatic/config.yaml']
    )
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        destination='dest',
        strip_components=1,
        user_runtime_directory='/borgmatic',
        ssh_command=None,
        local_path='borg7',
        remote_path='borg8',
        progress=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
    extract_process = flexmock(
        stdout=flexmock(
            read=lambda: '{"config_paths": ["borgmatic/config.yaml"]}',
        ),
    )
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process,
    ).once()

    module.run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version)


def test_run_bootstrap_translates_ssh_command_argument_to_config():
    config = {}
    flexmock(module).should_receive('make_bootstrap_config').and_return(config)
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').with_args(
        'repo',
        'archive',
        config,
        object,
        object,
        local_path='borg7',
        remote_path='borg8',
    ).and_return('archive')
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock(),
    )
    flexmock(module).should_receive('load_config_paths_from_archive').and_return(
        ['/borgmatic/config.yaml']
    )
    bootstrap_arguments = flexmock(
        repository='repo',
        archive='archive',
        destination='dest',
        strip_components=1,
        user_runtime_directory='/borgmatic',
        ssh_command='ssh -i key',
        local_path='borg7',
        remote_path='borg8',
        progress=None,
    )
    global_arguments = flexmock(
        dry_run=False,
    )
    local_borg_version = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob',
    ).replace_with(lambda path: path)
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
        {'progress': False},
        object,
        object,
        extract_to_stdout=False,
        destination_path='dest',
        strip_components=1,
        local_path='borg7',
        remote_path='borg8',
    ).and_return(extract_process).once()

    module.run_bootstrap(bootstrap_arguments, global_arguments, local_borg_version)
