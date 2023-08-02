import pytest
from flexmock import flexmock

from borgmatic.config import load as module


def test_probe_and_include_file_with_absolute_path_skips_probing():
    config = flexmock()
    flexmock(module).should_receive('load_configuration').with_args('/etc/include.yaml').and_return(
        config
    ).once()

    assert module.probe_and_include_file('/etc/include.yaml', ['/etc', '/var']) == config


def test_probe_and_include_file_with_relative_path_probes_include_directories():
    config = flexmock()
    flexmock(module.os.path).should_receive('exists').with_args('/etc/include.yaml').and_return(
        False
    )
    flexmock(module.os.path).should_receive('exists').with_args('/var/include.yaml').and_return(
        True
    )
    flexmock(module).should_receive('load_configuration').with_args('/etc/include.yaml').never()
    flexmock(module).should_receive('load_configuration').with_args('/var/include.yaml').and_return(
        config
    ).once()

    assert module.probe_and_include_file('include.yaml', ['/etc', '/var']) == config


def test_probe_and_include_file_with_relative_path_and_missing_files_raises():
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('load_configuration').never()

    with pytest.raises(FileNotFoundError):
        module.probe_and_include_file('include.yaml', ['/etc', '/var'])
