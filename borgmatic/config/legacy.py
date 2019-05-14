from collections import OrderedDict, namedtuple
from configparser import RawConfigParser

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
            option('one_file_system', value_type=bool, required=False),
            option('remote_path', required=False),
            option('repository'),
        ),
    ),
    Section_format(
        'storage',
        (
            option('encryption_passphrase', required=False),
            option('compression', required=False),
            option('umask', required=False),
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
    ),
    Section_format(
        'consistency', (option('checks', required=False), option('check_last', required=False))
    ),
)


def validate_configuration_format(parser, config_format):
    '''
    Given an open RawConfigParser and an expected config file format, validate that the parsed
    configuration file has the expected sections, that any required options are present in those
    sections, and that there aren't any unexpected options.

    A section is required if any of its contained options are required.

    Raise ValueError if anything is awry.
    '''
    section_names = set(parser.sections())
    required_section_names = tuple(
        section.name
        for section in config_format
        if any(option.required for option in section.options)
    )

    unknown_section_names = section_names - set(
        section_format.name for section_format in config_format
    )
    if unknown_section_names:
        raise ValueError(
            'Unknown config sections found: {}'.format(', '.join(unknown_section_names))
        )

    missing_section_names = set(required_section_names) - section_names
    if missing_section_names:
        raise ValueError('Missing config sections: {}'.format(', '.join(missing_section_names)))

    for section_format in config_format:
        if section_format.name not in section_names:
            continue

        option_names = parser.options(section_format.name)
        expected_options = section_format.options

        unexpected_option_names = set(option_names) - set(
            option.name for option in expected_options
        )

        if unexpected_option_names:
            raise ValueError(
                'Unexpected options found in config section {}: {}'.format(
                    section_format.name, ', '.join(sorted(unexpected_option_names))
                )
            )

        missing_option_names = tuple(
            option.name
            for option in expected_options
            if option.required
            if option.name not in option_names
        )

        if missing_option_names:
            raise ValueError(
                'Required options missing from config section {}: {}'.format(
                    section_format.name, ', '.join(missing_option_names)
                )
            )


def parse_section_options(parser, section_format):
    '''
    Given an open RawConfigParser and an expected section format, return the option values from that
    section as a dict mapping from option name to value. Omit those options that are not present in
    the parsed options.

    Raise ValueError if any option values cannot be coerced to the expected Python data type.
    '''
    type_getter = {str: parser.get, int: parser.getint, bool: parser.getboolean}

    return OrderedDict(
        (option.name, type_getter[option.value_type](section_format.name, option.name))
        for option in section_format.options
        if parser.has_option(section_format.name, option.name)
    )


def parse_configuration(config_filename, config_format):
    '''
    Given a config filename and an expected config file format, return the parsed configuration
    as a namedtuple with one attribute for each parsed section.

    Raise IOError if the file cannot be read, or ValueError if the format is not as expected.
    '''
    parser = RawConfigParser()
    if not parser.read(config_filename):
        raise ValueError('Configuration file cannot be opened: {}'.format(config_filename))

    validate_configuration_format(parser, config_format)

    # Describes a parsed configuration, where each attribute is the name of a configuration file
    # section and each value is a dict of that section's parsed options.
    Parsed_config = namedtuple(
        'Parsed_config', (section_format.name for section_format in config_format)
    )

    return Parsed_config(
        *(parse_section_options(parser, section_format) for section_format in config_format)
    )
