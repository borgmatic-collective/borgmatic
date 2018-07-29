import os

from flexmock import flexmock
import pytest

from borgmatic.commands import borgmatic as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    parser = module.parse_arguments()

    assert parser.config_paths == config_paths
    assert parser.excludes_filename == None
    assert parser.verbosity is None
    assert parser.json is False


def test_parse_arguments_with_path_arguments_overrides_defaults():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    parser = module.parse_arguments('--config', 'myconfig', '--excludes', 'myexcludes')

    assert parser.config_paths == ['myconfig']
    assert parser.excludes_filename == 'myexcludes'
    assert parser.verbosity is None


def test_parse_arguments_with_multiple_config_paths_parses_as_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    parser = module.parse_arguments('--config', 'myconfig', 'otherconfig')

    assert parser.config_paths == ['myconfig', 'otherconfig']
    assert parser.verbosity is None


def test_parse_arguments_with_verbosity_flag_overrides_default():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    parser = module.parse_arguments('--verbosity', '1')

    assert parser.config_paths == config_paths
    assert parser.excludes_filename == None
    assert parser.verbosity == 1


def test_parse_arguments_with_json_flag_overrides_default():
    parser = module.parse_arguments('--list', '--json')
    assert parser.json is True


def test_parse_arguments_with_no_actions_defaults_to_all_actions_enabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    parser = module.parse_arguments()

    assert parser.prune is True
    assert parser.create is True
    assert parser.check is True


def test_parse_arguments_with_prune_action_leaves_other_actions_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    parser = module.parse_arguments('--prune')

    assert parser.prune is True
    assert parser.create is False
    assert parser.check is False


def test_parse_arguments_with_multiple_actions_leaves_other_action_disabled():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    parser = module.parse_arguments('--create', '--check')

    assert parser.prune is False
    assert parser.create is True
    assert parser.check is True


def test_parse_arguments_with_invalid_arguments_exits():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    with pytest.raises(SystemExit):
        module.parse_arguments('--posix-me-harder')


def test_parse_arguments_with_json_flag_with_list_or_info_flag_does_not_raise_any_error():
    module.parse_arguments('--list', '--json')
    module.parse_arguments('--info', '--json')


def test_parse_arguments_with_json_flag_but_no_list_or_info_flag_raises_value_error():
    with pytest.raises(ValueError):
        module.parse_arguments('--json')


def test_parse_arguments_with_json_flag_and_both_list_and_info_flag_raises_value_error():
    with pytest.raises(ValueError):
        module.parse_arguments('--list', '--info', '--json')
