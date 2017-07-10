import os

from flexmock import flexmock
import pytest

from borgmatic.commands import borgmatic as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    flexmock(os.path).should_receive('exists').and_return(True)

    parser = module.parse_arguments()

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == module.DEFAULT_EXCLUDES_FILENAME
    assert parser.verbosity is None


def test_parse_arguments_with_filename_arguments_overrides_defaults():
    flexmock(os.path).should_receive('exists').and_return(True)

    parser = module.parse_arguments('--config', 'myconfig', '--excludes', 'myexcludes')

    assert parser.config_filename == 'myconfig'
    assert parser.excludes_filename == 'myexcludes'
    assert parser.verbosity is None


def test_parse_arguments_with_missing_default_excludes_file_sets_filename_to_none():
    flexmock(os.path).should_receive('exists').and_return(False)

    parser = module.parse_arguments()

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename is None
    assert parser.verbosity is None


def test_parse_arguments_with_missing_overridden_excludes_file_retains_filename():
    flexmock(os.path).should_receive('exists').and_return(False)

    parser = module.parse_arguments('--excludes', 'myexcludes')

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == 'myexcludes'
    assert parser.verbosity is None


def test_parse_arguments_with_verbosity_flag_overrides_default():
    flexmock(os.path).should_receive('exists').and_return(True)

    parser = module.parse_arguments('--verbosity', '1')

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == module.DEFAULT_EXCLUDES_FILENAME
    assert parser.verbosity == 1


def test_parse_arguments_with_invalid_arguments_exits():
    flexmock(os.path).should_receive('exists').and_return(True)

    with pytest.raises(SystemExit):
        module.parse_arguments('--posix-me-harder')
