import os

from flexmock import flexmock
import pytest

from borgmatic.commands import convert_config as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    flexmock(os.path).should_receive('exists').and_return(True)

    parser = module.parse_arguments()

    assert parser.source_config_filename == module.DEFAULT_SOURCE_CONFIG_FILENAME
    assert parser.source_excludes_filename == module.DEFAULT_SOURCE_EXCLUDES_FILENAME
    assert parser.destination_config_filename == module.DEFAULT_DESTINATION_CONFIG_FILENAME


def test_parse_arguments_with_filename_arguments_overrides_defaults():
    flexmock(os.path).should_receive('exists').and_return(True)

    parser = module.parse_arguments(
        '--source-config', 'config',
        '--source-excludes', 'excludes',
        '--destination-config', 'config.yaml',
    )

    assert parser.source_config_filename == 'config'
    assert parser.source_excludes_filename == 'excludes'
    assert parser.destination_config_filename == 'config.yaml'


def test_parse_arguments_with_missing_default_excludes_file_sets_filename_to_none():
    flexmock(os.path).should_receive('exists').and_return(False)

    parser = module.parse_arguments()

    assert parser.source_config_filename == module.DEFAULT_SOURCE_CONFIG_FILENAME
    assert parser.source_excludes_filename is None
    assert parser.destination_config_filename == module.DEFAULT_DESTINATION_CONFIG_FILENAME


def test_parse_arguments_with_invalid_arguments_exits():
    flexmock(os.path).should_receive('exists').and_return(True)

    with pytest.raises(SystemExit):
        module.parse_arguments('--posix-me-harder')
