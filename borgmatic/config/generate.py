import collections
import io
import os
import re

from ruamel import yaml

from borgmatic.config import load

INDENT = 4
SEQUENCE_INDENT = 2


def _insert_newline_before_comment(config, field_name):
    '''
    Using some ruamel.yaml black magic, insert a blank line in the config right before the given
    field and its comments.
    '''
    config.ca.items[field_name][1].insert(
        0, yaml.tokens.CommentToken('\n', yaml.error.CommentMark(0), None)
    )


def _schema_to_sample_configuration(schema, level=0, parent_is_sequence=False):
    '''
    Given a loaded configuration schema, generate and return sample config for it. Include comments
    for each section based on the schema "description".
    '''
    schema_type = schema.get('type')
    example = schema.get('example')
    if example is not None:
        return example

    if schema_type == 'array':
        config = yaml.comments.CommentedSeq(
            [_schema_to_sample_configuration(schema['items'], level, parent_is_sequence=True)]
        )
        add_comments_to_configuration_sequence(config, schema, indent=(level * INDENT))
    elif schema_type == 'object':
        config = yaml.comments.CommentedMap(
            [
                (field_name, _schema_to_sample_configuration(sub_schema, level + 1))
                for field_name, sub_schema in schema['properties'].items()
            ]
        )
        indent = (level * INDENT) + (SEQUENCE_INDENT if parent_is_sequence else 0)
        add_comments_to_configuration_object(
            config, schema, indent=indent, skip_first=parent_is_sequence
        )
    else:
        raise ValueError('Schema at level {} is unsupported: {}'.format(level, schema))

    return config


def _comment_out_line(line):
    # If it's already is commented out (or empty), there's nothing further to do!
    stripped_line = line.lstrip()
    if not stripped_line or stripped_line.startswith('#'):
        return line

    # Comment out the names of optional sections, inserting the '#' after any indent for aesthetics.
    matches = re.match(r'(\s*)', line)
    indent_spaces = matches.group(0) if matches else ''
    count_indent_spaces = len(indent_spaces)

    return '# '.join((indent_spaces, line[count_indent_spaces:]))


def _comment_out_optional_configuration(rendered_config):
    '''
    Post-process a rendered configuration string to comment out optional key/values, as determined
    by a sentinel in the comment before each key.

    The idea is that the pre-commented configuration prevents the user from having to comment out a
    bunch of configuration they don't care about to get to a minimal viable configuration file.

    Ideally ruamel.yaml would support commenting out keys during configuration generation, but it's
    not terribly easy to accomplish that way.
    '''
    lines = []
    optional = False

    for line in rendered_config.split('\n'):
        # Upon encountering an optional configuration option, comment out lines until the next blank
        # line.
        if line.strip().startswith('# {}'.format(COMMENTED_OUT_SENTINEL)):
            optional = True
            continue

        # Hit a blank line, so reset commenting.
        if not line.strip():
            optional = False

        lines.append(_comment_out_line(line) if optional else line)

    return '\n'.join(lines)


def render_configuration(config):
    '''
    Given a config data structure of nested OrderedDicts, render the config as YAML and return it.
    '''
    dumper = yaml.YAML()
    dumper.indent(mapping=INDENT, sequence=INDENT + SEQUENCE_INDENT, offset=INDENT)
    rendered = io.StringIO()
    dumper.dump(config, rendered)

    return rendered.getvalue()


def write_configuration(config_filename, rendered_config, mode=0o600):
    '''
    Given a target config filename and rendered config YAML, write it out to file. Create any
    containing directories as needed.
    '''
    if os.path.exists(config_filename):
        raise FileExistsError('{} already exists. Aborting.'.format(config_filename))

    try:
        os.makedirs(os.path.dirname(config_filename), mode=0o700)
    except (FileExistsError, FileNotFoundError):
        pass

    with open(config_filename, 'w') as config_file:
        config_file.write(rendered_config)

    os.chmod(config_filename, mode)


def add_comments_to_configuration_sequence(config, schema, indent=0):
    '''
    If the given config sequence's items are object, then mine the schema for the description of the
    object's first item, and slap that atop the sequence. Indent the comment the given number of
    characters.

    Doing this for sequences of maps results in nice comments that look like:

    ```
    things:
        # First key description. Added by this function.
        - key: foo
          # Second key description. Added by add_comments_to_configuration_object().
          other: bar
    ```
    '''
    if schema['items'].get('type') != 'object':
        return

    for field_name in config[0].keys():
        field_schema = schema['items']['properties'].get(field_name, {})
        description = field_schema.get('description')

        # No description to use? Skip it.
        if not field_schema or not description:
            return

        config[0].yaml_set_start_comment(description, indent=indent)

        # We only want the first key's description here, as the rest of the keys get commented by
        # add_comments_to_configuration_object().
        return


REQUIRED_SECTION_NAMES = {'location', 'retention'}
REQUIRED_KEYS = {'source_directories', 'repositories', 'keep_daily'}
COMMENTED_OUT_SENTINEL = 'COMMENT_OUT'


def add_comments_to_configuration_object(config, schema, indent=0, skip_first=False):
    '''
    Using descriptions from a schema as a source, add those descriptions as comments to the given
    config mapping, before each field. Indent the comment the given number of characters.
    '''
    for index, field_name in enumerate(config.keys()):
        if skip_first and index == 0:
            continue

        field_schema = schema['properties'].get(field_name, {})
        description = field_schema.get('description', '').strip()

        # If this is an optional key, add an indicator to the comment flagging it to be commented
        # out from the sample configuration. This sentinel is consumed by downstream processing that
        # does the actual commenting out.
        if field_name not in REQUIRED_SECTION_NAMES and field_name not in REQUIRED_KEYS:
            description = (
                '\n'.join((description, COMMENTED_OUT_SENTINEL))
                if description
                else COMMENTED_OUT_SENTINEL
            )

        # No description to use? Skip it.
        if not field_schema or not description:  # pragma: no cover
            continue

        config.yaml_set_comment_before_after_key(key=field_name, before=description, indent=indent)

        if index > 0:
            _insert_newline_before_comment(config, field_name)


RUAMEL_YAML_COMMENTS_INDEX = 1


def remove_commented_out_sentinel(config, field_name):
    '''
    Given a configuration CommentedMap and a top-level field name in it, remove any "commented out"
    sentinel found at the end of its YAML comments. This prevents the given field name from getting
    commented out by downstream processing that consumes the sentinel.
    '''
    try:
        last_comment_value = config.ca.items[field_name][RUAMEL_YAML_COMMENTS_INDEX][-1].value
    except KeyError:
        return

    if last_comment_value == '# {}\n'.format(COMMENTED_OUT_SENTINEL):
        config.ca.items[field_name][RUAMEL_YAML_COMMENTS_INDEX].pop()


def merge_source_configuration_into_destination(destination_config, source_config):
    '''
    Deep merge the given source configuration dict into the destination configuration CommentedMap,
    favoring values from the source when there are collisions.

    The purpose of this is to upgrade configuration files from old versions of borgmatic by adding
    new
    configuration keys and comments.
    '''
    if not source_config:
        return destination_config
    if not destination_config or not isinstance(source_config, collections.abc.Mapping):
        return source_config

    for field_name, source_value in source_config.items():
        # Since this key/value is from the source configuration, leave it uncommented and remove any
        # sentinel that would cause it to get commented out.
        remove_commented_out_sentinel(destination_config, field_name)

        # This is a mapping. Recurse for this key/value.
        if isinstance(source_value, collections.abc.Mapping):
            destination_config[field_name] = merge_source_configuration_into_destination(
                destination_config[field_name], source_value
            )
            continue

        # This is a sequence. Recurse for each item in it.
        if isinstance(source_value, collections.abc.Sequence) and not isinstance(source_value, str):
            destination_value = destination_config[field_name]
            destination_config[field_name] = yaml.comments.CommentedSeq(
                [
                    merge_source_configuration_into_destination(
                        destination_value[index] if index < len(destination_value) else None,
                        source_item,
                    )
                    for index, source_item in enumerate(source_value)
                ]
            )
            continue

        # This is some sort of scalar. Simply set it into the destination.
        destination_config[field_name] = source_config[field_name]

    return destination_config


def generate_sample_configuration(source_filename, destination_filename, schema_filename):
    '''
    Given an optional source configuration filename, and a required destination configuration
    filename, and the path to a schema filename in a YAML rendition of the JSON Schema format,
    write out a sample configuration file based on that schema. If a source filename is provided,
    merge the parsed contents of that configuration into the generated configuration.
    '''
    schema = yaml.round_trip_load(open(schema_filename))
    source_config = None

    if source_filename:
        source_config = load.load_configuration(source_filename)

    destination_config = merge_source_configuration_into_destination(
        _schema_to_sample_configuration(schema), source_config
    )

    write_configuration(
        destination_filename,
        _comment_out_optional_configuration(render_configuration(destination_config)),
    )
