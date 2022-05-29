from borgmatic.commands import generate_config as module


def test_parse_arguments_with_no_arguments_uses_default_destination():
    parser = module.parse_arguments()

    assert parser.destination_filename == module.DEFAULT_DESTINATION_CONFIG_FILENAME


def test_parse_arguments_with_destination_argument_overrides_default():
    parser = module.parse_arguments('--destination', 'config.yaml')

    assert parser.destination_filename == 'config.yaml'


def test_parse_arguments_parses_source():
    parser = module.parse_arguments('--source', 'source.yaml', '--destination', 'config.yaml')

    assert parser.source_filename == 'source.yaml'


def test_parse_arguments_parses_overwrite():
    parser = module.parse_arguments('--destination', 'config.yaml', '--overwrite')

    assert parser.overwrite
