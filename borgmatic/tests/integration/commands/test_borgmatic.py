import os

from flexmock import flexmock
import pytest

from borgmatic.commands import borgmatic as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    parser = module.parse_arguments()

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == None
    assert parser.verbosity is None


def test_parse_arguments_with_filename_arguments_overrides_defaults():
    parser = module.parse_arguments('--config', 'myconfig', '--excludes', 'myexcludes')

    assert parser.config_filename == 'myconfig'
    assert parser.excludes_filename == 'myexcludes'
    assert parser.verbosity is None


def test_parse_arguments_with_verbosity_flag_overrides_default():
    parser = module.parse_arguments('--verbosity', '1')

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == None
    assert parser.verbosity == 1


def test_parse_arguments_with_invalid_arguments_exits():
    with pytest.raises(SystemExit):
        module.parse_arguments('--posix-me-harder')
