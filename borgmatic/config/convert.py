import os

from ruamel import yaml

from borgmatic.config import generate


def _convert_section(source_section_config, section_schema):
    '''
    Given a legacy Parsed_config instance for a single section, convert it to its corresponding
    yaml.comments.CommentedMap representation in preparation for actual serialization to YAML.

    Where integer types exist in the given section schema, convert their values to integers.
    '''
    destination_section_config = yaml.comments.CommentedMap([
        (
            option_name,
            int(option_value)
                if section_schema['map'].get(option_name, {}).get('type') == 'int' else option_value
        )
        for option_name, option_value in source_section_config.items()
    ])

    return destination_section_config


def convert_legacy_parsed_config(source_config, source_excludes, schema):
    '''
    Given a legacy Parsed_config instance loaded from an INI-style config file and a list of exclude
    patterns, convert them to a corresponding yaml.comments.CommentedMap representation in
    preparation for serialization to a single YAML config file.

    Additionally, use the given schema as a source of helpful comments to include within the
    returned CommentedMap.
    '''
    destination_config = yaml.comments.CommentedMap([
        (section_name, _convert_section(section_config, schema['map'][section_name]))
        for section_name, section_config in source_config._asdict().items()
    ])

    # Split space-seperated values into actual lists, make "repository" into a list, and merge in
    # excludes.
    location = destination_config['location']
    location['source_directories'] = source_config.location['source_directories'].split(' ')
    location['repositories'] = [location.pop('repository')]
    location['exclude_patterns'] = source_excludes

    if source_config.consistency.get('checks'):
        destination_config['consistency']['checks'] = source_config.consistency['checks'].split(' ')

    # Add comments to each section, and then add comments to the fields in each section.
    generate.add_comments_to_configuration(destination_config, schema)

    for section_name, section_config in destination_config.items():
        generate.add_comments_to_configuration(
            section_config,
            schema['map'][section_name],
            indent=generate.INDENT,
        )

    return destination_config


class LegacyConfigurationNotUpgraded(FileNotFoundError):
    def __init__(self):
        super(LegacyConfigurationNotUpgraded, self).__init__(
            '''borgmatic changed its configuration file format in version 1.1.0 from INI-style
to YAML. This better supports validation, and has a more natural way to express
lists of values. To upgrade your existing configuration, run:

    sudo upgrade-borgmatic-config

That will generate a new YAML configuration file at /etc/borgmatic/config.yaml
(by default) using the values from both your existing configuration and excludes
files. The new version of borgmatic will consume the YAML configuration file
instead of the old one.'''
        )


def guard_configuration_upgraded(source_config_filename, destination_config_filenames):
    '''
    If legacy source configuration exists but no destination upgraded configs do, raise
    LegacyConfigurationNotUpgraded.

    The idea is that we want to alert the user about upgrading their config if they haven't already.
    '''
    destination_config_exists = any(
        os.path.exists(filename)
        for filename in destination_config_filenames
    )

    if os.path.exists(source_config_filename) and not destination_config_exists:
        raise LegacyConfigurationNotUpgraded()


class LegacyExcludesFilenamePresent(FileNotFoundError):
    def __init__(self):
        super(LegacyExcludesFilenamePresent, self).__init__(
            '''borgmatic changed its configuration file format in version 1.1.0 from INI-style
to YAML. This better supports validation, and has a more natural way to express
lists of values. The new configuration file incorporates excludes, so you no
longer need to provide an excludes filename on the command-line with an
"--excludes" argument.

Please remove the "--excludes" argument and run borgmatic again.'''
        )


def guard_excludes_filename_omitted(excludes_filename):
    if excludes_filename != None:
        raise LegacyExcludesFilenamePresent()
