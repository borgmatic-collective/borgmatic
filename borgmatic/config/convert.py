from ruamel import yaml

from borgmatic.config import generate


def _convert_section(source_section_config, section_schema):
    '''
    Given a legacy Parsed_config instance for a single section, convert it to its corresponding
    yaml.comments.CommentedMap representation in preparation for actual serialization to YAML.

    Additionally, use the section schema as a source of helpful comments to include within the
    returned CommentedMap.
    '''
    destination_section_config = yaml.comments.CommentedMap(source_section_config)
    generate.add_comments_to_configuration(destination_section_config, section_schema, indent=generate.INDENT)

    return destination_section_config


def convert_legacy_parsed_config(source_config, schema):
    '''
    Given a legacy Parsed_config instance loaded from an INI-style config file, convert it to its
    corresponding yaml.comments.CommentedMap representation in preparation for actual serialization
    to YAML.

    Additionally, use the given schema as a source of helpful comments to include within the
    returned CommentedMap.
    '''
    destination_config = yaml.comments.CommentedMap([
        (section_name, _convert_section(section_config, schema['map'][section_name]))
        for section_name, section_config in source_config._asdict().items()
    ])

    destination_config['location']['source_directories'] = source_config.location['source_directories'].split(' ')

    if source_config.consistency['checks']:
        destination_config['consistency']['checks'] = source_config.consistency['checks'].split(' ')

    generate.add_comments_to_configuration(destination_config, schema)

    return destination_config
