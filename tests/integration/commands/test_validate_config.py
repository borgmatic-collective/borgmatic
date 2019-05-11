from flexmock import flexmock

from borgmatic.commands import validate_config as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    config_paths = ['default']
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(config_paths)

    parser = module.parse_arguments()

    assert parser.config_paths == config_paths


def test_parse_arguments_with_multiple_config_paths_parses_as_list():
    flexmock(module.collect).should_receive('get_default_config_paths').and_return(['default'])

    parser = module.parse_arguments('--config', 'myconfig', 'otherconfig')

    assert parser.config_paths == ['myconfig', 'otherconfig']
