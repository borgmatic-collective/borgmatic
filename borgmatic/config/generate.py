from collections import OrderedDict

from ruamel import yaml


INDENT = 4


def write_configuration(config_filename, config):
    '''
    Given a target config filename and a config data structure of nested OrderedDicts, write out the
    config to file as YAML.
    '''
    with open(config_filename, 'w') as config_file:
        config_file.write(yaml.round_trip_dump(config, indent=INDENT, block_seq_indent=INDENT))


def _insert_newline_before_comment(config, field_name):
    '''
    Using some ruamel.yaml black magic, insert a blank line in the config right befor the given
    field and its comments.
    '''
    config.ca.items[field_name][1].insert(
        0,
        yaml.tokens.CommentToken('\n', yaml.error.CommentMark(0), None),
    )


def add_comments_to_configuration(config, schema, indent=0):
    '''
    Using descriptions from a schema as a source, add those descriptions as comments to the given
    config before each field. This function only adds comments for the top-most config map level.
    Indent the comment the given number of characters.
    '''
    for index, field_name in enumerate(config.keys()):
        field_schema = schema['map'].get(field_name, {})
        description = field_schema.get('desc')

        # No description to use? Skip it.
        if not schema or not description:
            continue

        config.yaml_set_comment_before_after_key(
            key=field_name,
            before=description,
            indent=indent,
        )
        if index > 0:
            _insert_newline_before_comment(config, field_name)


def _section_schema_to_sample_configuration(section_schema):
    '''
    Given the schema for a particular config section, generate and return sample config for that
    section. Include comments for each field based on the schema "desc" description.
    '''
    section_config = yaml.comments.CommentedMap([
        (field_name, field_schema['example'])
        for field_name, field_schema in section_schema['map'].items()
    ])

    add_comments_to_configuration(section_config, section_schema, indent=INDENT)

    return section_config


def _schema_to_sample_configuration(schema):
    '''
    Given a loaded configuration schema, generate and return sample config for it. Include comments
    for each section based on the schema "desc" description.
    '''
    config = yaml.comments.CommentedMap([
        (section_name, _section_schema_to_sample_configuration(section_schema))
        for section_name, section_schema in schema['map'].items()
    ])

    add_comments_to_configuration(config, schema)

    return config


def generate_sample_configuration(config_filename, schema_filename):
    '''
    Given a target config filename and the path to a schema filename in pykwalify YAML schema
    format, write out a sample configuration file based on that schema.
    '''
    schema = yaml.round_trip_load(open(schema_filename))
    config = _schema_to_sample_configuration(schema)

    write_configuration(config_filename, config)
