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

    # Split space-seperated values into actual lists, and merge in excludes.
    destination_config['location']['source_directories'] = source_config.location['source_directories'].split(' ')
    destination_config['location']['exclude_patterns'] = source_excludes

    if source_config.consistency['checks']:
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
