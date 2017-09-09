import os

from flexmock import flexmock
import pytest

from borgmatic.commands import borgmatic as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    parser = module.parse_arguments()

    assert parser.config_paths == module.collect.DEFAULT_CONFIG_PATHS
    assert parser.excludes_filename == None
    assert parser.verbosity is None


def test_parse_arguments_with_path_arguments_overrides_defaults():
    parser = module.parse_arguments('--config', 'myconfig', '--excludes', 'myexcludes')

    assert parser.config_paths == ['myconfig']
    assert parser.excludes_filename == 'myexcludes'
    assert parser.verbosity is None


def test_parse_arguments_with_multiple_config_paths_parses_as_list():
    parser = module.parse_arguments('--config', 'myconfig', 'otherconfig')

    assert parser.config_paths == ['myconfig', 'otherconfig']
    assert parser.verbosity is None


def test_parse_arguments_with_verbosity_flag_overrides_default():
    parser = module.parse_arguments('--verbosity', '1')

    assert parser.config_paths == module.collect.DEFAULT_CONFIG_PATHS
    assert parser.excludes_filename == None
    assert parser.verbosity == 1


def test_parse_arguments_with_no_actions_defaults_to_all_actions_enabled():
    parser = module.parse_arguments()

    assert parser.prune is True
    assert parser.create is True
    assert parser.check is True


def test_parse_arguments_with_prune_action_leaves_other_actions_disabled():
    parser = module.parse_arguments('--prune')

    assert parser.prune is True
    assert parser.create is False
    assert parser.check is False


def test_parse_arguments_with_multiple_actions_leaves_other_action_disabled():
    parser = module.parse_arguments('--create', '--check')

    assert parser.prune is False
    assert parser.create is True
    assert parser.check is True


def test_parse_arguments_with_invalid_arguments_exits():
    with pytest.raises(SystemExit):
        module.parse_arguments('--posix-me-harder')
