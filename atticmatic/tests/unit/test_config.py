from flexmock import flexmock
from nose.tools import assert_raises

from atticmatic import config as module


def insert_mock_parser(section_names):
    parser = flexmock()
    parser.should_receive('read')
    parser.should_receive('sections').and_return(section_names)
    flexmock(module).SafeConfigParser = parser

    return parser


def test_parse_configuration_should_return_config_data():
    section_names = (module.CONFIG_SECTION_LOCATION, module.CONFIG_SECTION_RETENTION)
    parser = insert_mock_parser(section_names)

    for section_name in section_names:
        parser.should_receive('options').with_args(section_name).and_return(
            module.CONFIG_FORMAT[section_name],
        )

    expected_config = (
        module.LocationConfig(flexmock(), flexmock()),
        module.RetentionConfig(flexmock(), flexmock(), flexmock()),
    )
    sections = (
        (module.CONFIG_SECTION_LOCATION, expected_config[0], 'get'),
        (module.CONFIG_SECTION_RETENTION, expected_config[1], 'getint'),
    )

    for section_name, section_config, method_name in sections:
        for index, option_name in enumerate(module.CONFIG_FORMAT[section_name]):
            (
                parser.should_receive(method_name).with_args(section_name, option_name)
                .and_return(section_config[index])
            )

    config = module.parse_configuration(flexmock())

    assert config == expected_config


def test_parse_configuration_with_missing_section_should_raise():
    insert_mock_parser((module.CONFIG_SECTION_LOCATION,))

    with assert_raises(ValueError):
        module.parse_configuration(flexmock())


def test_parse_configuration_with_extra_section_should_raise():
    insert_mock_parser((module.CONFIG_SECTION_LOCATION, module.CONFIG_SECTION_RETENTION, 'extra'))

    with assert_raises(ValueError):
        module.parse_configuration(flexmock())


def test_parse_configuration_with_missing_option_should_raise():
    section_names = (module.CONFIG_SECTION_LOCATION, module.CONFIG_SECTION_RETENTION)
    parser = insert_mock_parser(section_names)

    for section_name in section_names:
        parser.should_receive('options').with_args(section_name).and_return(
            module.CONFIG_FORMAT[section_name][:-1],
        )

    with assert_raises(ValueError):
        module.parse_configuration(flexmock())


def test_parse_configuration_with_extra_option_should_raise():
    section_names = (module.CONFIG_SECTION_LOCATION, module.CONFIG_SECTION_RETENTION)
    parser = insert_mock_parser(section_names)

    for section_name in section_names:
        parser.should_receive('options').with_args(section_name).and_return(
            module.CONFIG_FORMAT[section_name] + ('extra',),
        )

    with assert_raises(ValueError):
        module.parse_configuration(flexmock())
