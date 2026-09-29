import pytest
from flexmock import flexmock

from borgmatic.config import load as module


def test_probe_and_include_file_with_absolute_path_skips_probing():
    config = flexmock()
    config_paths = set()
    flexmock(module).should_receive('load_configuration').with_args(
        '/etc/include.yaml',
        config_paths,
    ).and_return(config).once()

    assert (
        module.probe_and_include_file('/etc/include.yaml', ['/etc', '/var'], config_paths) == config
    )


def test_probe_and_include_file_with_relative_path_probes_include_directories():
    config = {'foo': 'bar'}
    config_paths = set()
    flexmock(module.os.path).should_receive('exists').with_args('/etc/include.yaml').and_return(
        False,
    )
    flexmock(module.os.path).should_receive('exists').with_args('/var/include.yaml').and_return(
        True,
    )
    flexmock(module).should_receive('load_configuration').with_args(
        '/etc/include.yaml',
        config_paths,
    ).never()
    flexmock(module).should_receive('load_configuration').with_args(
        '/var/include.yaml',
        config_paths,
    ).and_return(config).once()

    assert module.probe_and_include_file('include.yaml', ['/etc', '/var'], config_paths) == {
        'foo': 'bar',
    }


def test_probe_and_include_file_with_relative_path_and_missing_files_raises():
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('load_configuration').never()

    with pytest.raises(FileNotFoundError):
        module.probe_and_include_file('include.yaml', ['/etc', '/var'], config_paths=set())


def test_merge_repository_configuration_skips_repository_specific_options():
    assert module.merge_repository_configuration(
        repository_config={'path': '/foo', 'label': 'foo', 'remote_path': 'borg2'},
        config={'stuff': 'such'},
    ) == {'stuff': 'such', 'remote_path': 'borg2'}


def test_merge_repository_configuration_overwrites_config_options():
    assert module.merge_repository_configuration(
        repository_config={'remote_path': 'borg2'},
        config={'stuff': 'such', 'remote_path': 'borg1'},
    ) == {'stuff': 'such', 'remote_path': 'borg2'}


def test_merge_repository_configuration_deep_copies_configuration():
    config = {'stuff': {'nested': 'data'}}
    merged_config = module.merge_repository_configuration(
        repository_config={'path': '/foo', 'label': 'foo'},
        config=config,
    )

    assert merged_config == {'stuff': {'nested': 'data'}}
    merged_config['stuff']['nested'] = 'changed'
    assert merged_config == {'stuff': {'nested': 'changed'}}
    assert config == {'stuff': {'nested': 'data'}}
