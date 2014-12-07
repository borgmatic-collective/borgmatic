from collections import OrderedDict, namedtuple

try:
    # Python 2
    from ConfigParser import ConfigParser
except ImportError:
    # Python 3
    from configparser import ConfigParser


Section_format = namedtuple('Section_format', ('name', 'options'))
Config_option = namedtuple('Config_option', ('name', 'value_type', 'required'))


def option(name, value_type=str, required=True):
    '''
    Given a config file option name, an expected type for its value, and whether it's required,
    return a Config_option capturing that information.
    '''
    return Config_option(name, value_type, required)


CONFIG_FORMAT = (
    Section_format(
        'location',
        (
            option('source_directories'),
            option('repository'),
        ),
    ),
    Section_format(
        'retention',
        (
            option('keep_within', required=False),
            option('keep_hourly', int, required=False),
            option('keep_daily', int, required=False),
            option('keep_weekly', int, required=False),
            option('keep_monthly', int, required=False),
            option('keep_yearly', int, required=False),
            option('prefix', required=False),
        ),
    )
)


def validate_configuration_format(parser, config_format):
    '''
    Given an open ConfigParser and an expected config file format, validate that the parsed
    configuration file has the expected sections, that any required options are present in those
    sections, and that there aren't any unexpected options.

    Raise ValueError if anything is awry.
    '''
    section_names = parser.sections()
    required_section_names = tuple(section.name for section in config_format)

    if set(section_names) != set(required_section_names):
        raise ValueError(
            'Expected config sections {} but found sections: {}'.format(
                ', '.join(required_section_names),
                ', '.join(section_names)
            )
        )

    for section_format in config_format:
        option_names = parser.options(section_format.name)
        expected_options = section_format.options

        unexpected_option_names = set(option_names) - set(option.name for option in expected_options)

        if unexpected_option_names:
            raise ValueError(
                'Unexpected options found in config section {}: {}'.format(
                    section_format.name,
                    ', '.join(sorted(unexpected_option_names)),
                )
            )

        missing_option_names = tuple(
            option.name for option in expected_options if option.required
            if option.name not in option_names
        )

        if missing_option_names:
            raise ValueError(
                'Required options missing from config section {}: {}'.format(
                    section_format.name,
                    ', '.join(missing_option_names)
                )
            )


def parse_section_options(parser, section_format):
    '''
    Given an open ConfigParser and an expected section format, return the option values from that
    section as a dict mapping from option name to value. Omit those options that are not present in
    the parsed options.

    Raise ValueError if any option values cannot be coerced to the expected Python data type.
    '''
    type_getter = {
        str: parser.get,
        int: parser.getint,
    }

    return OrderedDict(
        (option.name, type_getter[option.value_type](section_format.name, option.name))
        for option in section_format.options
        if parser.has_option(section_format.name, option.name)
    )


def parse_configuration(config_filename):
    '''
    Given a config filename of the expected format, return the parsed configuration as a tuple of
    (location config, retention config) where each config is a dict of that section's options.

    Raise IOError if the file cannot be read, or ValueError if the format is not as expected.
    '''
    parser = ConfigParser()
    parser.readfp(open(config_filename))

    validate_configuration_format(parser, CONFIG_FORMAT)

    return tuple(
        parse_section_options(parser, section_format)
        for section_format in CONFIG_FORMAT
    )
