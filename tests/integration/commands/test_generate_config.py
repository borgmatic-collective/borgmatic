from borgmatic.commands import generate_config as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    parser = module.parse_arguments()

    assert parser.destination_filename == module.DEFAULT_DESTINATION_CONFIG_FILENAME


def test_parse_arguments_with_filename_argument_overrides_defaults():
    parser = module.parse_arguments('--destination', 'config.yaml')

    assert parser.destination_filename == 'config.yaml'
