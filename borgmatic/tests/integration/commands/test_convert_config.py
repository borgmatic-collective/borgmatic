from borgmatic.commands import convert_config as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    parser = module.parse_arguments()

    assert parser.source_filename == module.DEFAULT_SOURCE_CONFIG_FILENAME
    assert parser.destination_filename == module.DEFAULT_DESTINATION_CONFIG_FILENAME

def test_parse_arguments_with_filename_arguments_overrides_defaults():
    parser = module.parse_arguments('--source', 'config', '--destination', 'config.yaml')

    assert parser.source_filename == 'config'
    assert parser.destination_filename == 'config.yaml'
