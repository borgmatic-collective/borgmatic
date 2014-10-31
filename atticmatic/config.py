from collections import namedtuple
from ConfigParser import SafeConfigParser


CONFIG_SECTION_LOCATION = 'location'
CONFIG_SECTION_RETENTION = 'retention'

CONFIG_FORMAT = {
    CONFIG_SECTION_LOCATION: ('source_directories', 'repository'),
    CONFIG_SECTION_RETENTION: ('keep_daily', 'keep_weekly', 'keep_monthly'),
}

LocationConfig = namedtuple('LocationConfig', CONFIG_FORMAT[CONFIG_SECTION_LOCATION])
RetentionConfig = namedtuple('RetentionConfig', CONFIG_FORMAT[CONFIG_SECTION_RETENTION])


def parse_configuration(config_filename):
    '''
    Given a config filename of the expected format, return the parse configuration as a tuple of
    (LocationConfig, RetentionConfig). Raise if the format is not as expected.
    '''
    parser = SafeConfigParser()
    parser.read((config_filename,))
    section_names = parser.sections()
    expected_section_names = CONFIG_FORMAT.keys()

    if set(section_names) != set(expected_section_names):
        raise ValueError(
            'Expected config sections {} but found sections: {}'.format(
                ', '.join(expected_section_names),
                ', '.join(section_names)
            )
        )

    for section_name in section_names:
        option_names = parser.options(section_name)
        expected_option_names = CONFIG_FORMAT[section_name]

        if set(option_names) != set(expected_option_names):
            raise ValueError(
                'Expected options {} in config section {} but found options: {}'.format(
                    ', '.join(expected_option_names),
                    section_name,
                    ', '.join(option_names)
                )
            )

    return (
        LocationConfig(*(
            parser.get(CONFIG_SECTION_LOCATION, option_name)
            for option_name in CONFIG_FORMAT[CONFIG_SECTION_LOCATION]
        )),
        RetentionConfig(*(
            parser.getint(CONFIG_SECTION_RETENTION, option_name)
            for option_name in CONFIG_FORMAT[CONFIG_SECTION_RETENTION]
        ))
    )
