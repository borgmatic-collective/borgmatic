import collections
import io
import os
import re

import ruamel.yaml

import borgmatic.config.schema
from borgmatic.config import load, normalize

INDENT = 4
SEQUENCE_INDENT = 2


def insert_newline_before_comment(config, field_name):
    '''
    Using some ruamel.yaml black magic, insert a blank line in the config right before the given
    field and its comments.
    '''
    config.ca.items[field_name][1].insert(
        0, ruamel.yaml.tokens.CommentToken('\n', ruamel.yaml.error.CommentMark(0), None)
    )


SCALAR_SCHEMA_TYPES = {'string', 'boolean', 'integer', 'number'}


def schema_to_sample_configuration(schema, source_config=None, level=0, parent_is_sequence=False):
    '''
    Given a loaded configuration schema and a source configuration, generate and return sample
    config for the schema. Include comments for each option based on the schema "description".

    If a source config is given, walk it alongside the given schema so that both can be taken into
    account when commenting out particular options in add_comments_to_configuration_object().
    '''
    schema_type = schema.get('type')
    example = schema.get('example')

    if borgmatic.config.schema.compare_types(schema_type, {'array'}):
        config = ruamel.yaml.comments.CommentedSeq(
            example
            if borgmatic.config.schema.compare_types(
                schema['items'].get('type'), SCALAR_SCHEMA_TYPES
            )
            else [
                schema_to_sample_configuration(
                    schema['items'], source_config, level, parent_is_sequence=True
                )
            ]
        )
        add_comments_to_configuration_sequence(config, schema, indent=(level * INDENT))
    elif borgmatic.config.schema.compare_types(schema_type, {'object'}):
        if source_config and isinstance(source_config, list) and isinstance(source_config[0], dict):
            source_config = source_config[0]

        config = (
            ruamel.yaml.comments.CommentedMap(
                [
                    (
                        field_name,
                        schema_to_sample_configuration(
                            sub_schema, (source_config or {}).get(field_name, {}), level + 1
                        ),
                    )
                    for field_name, sub_schema in borgmatic.config.schema.get_properties(
                        schema
                    ).items()
                ]
            )
            or example
        )
        indent = (level * INDENT) + (SEQUENCE_INDENT if parent_is_sequence else 0)
        add_comments_to_configuration_object(
            config, schema, source_config, indent=indent, skip_first_field=parent_is_sequence
        )
    elif borgmatic.config.schema.compare_types(schema_type, SCALAR_SCHEMA_TYPES, match=all):
        return example
    else:
        raise ValueError(f'Schema at level {level} is unsupported: {schema}')

    return config


def comment_out_line(line):
    # If it's already is commented out (or empty), there's nothing further to do!
    stripped_line = line.lstrip()
    if not stripped_line or stripped_line.startswith('#'):
        return line

    # Comment out the names of optional options, inserting the '#' after any indent for aesthetics.
    matches = re.match(r'(\s*)', line)
    indent_spaces = matches.group(0) if matches else ''
    count_indent_spaces = len(indent_spaces)

    return '# '.join((indent_spaces, line[count_indent_spaces:]))


def comment_out_optional_configuration(rendered_config):
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
    indent_characters = None
    indent_characters_at_sentinel = None

    for line in rendered_config.split('\n'):
        indent_characters = len(line) - len(line.lstrip())

        # Upon encountering an optional configuration option, comment out lines until the next blank
        # line.
        if line.strip().startswith(f'# {COMMENTED_OUT_SENTINEL}'):
            optional = True
            indent_characters_at_sentinel = indent_characters
            continue

        # Hit a blank line, so reset commenting.
        if not line.strip():
            optional = False
            indent_characters_at_sentinel = None
        # Dedented, so reset commenting.
        elif (
            indent_characters_at_sentinel is not None
            and indent_characters < indent_characters_at_sentinel
        ):
            optional = False
            indent_characters_at_sentinel = None

        lines.append(comment_out_line(line) if optional else line)

    return '\n'.join(lines)


def render_configuration(config):
    '''
    Given a config data structure of nested OrderedDicts, render the config as YAML and return it.
    '''
    dumper = ruamel.yaml.YAML(typ='rt')
    dumper.indent(mapping=INDENT, sequence=INDENT + SEQUENCE_INDENT, offset=INDENT)
    rendered = io.StringIO()
    dumper.dump(config, rendered)

    return rendered.getvalue()


def write_configuration(config_filename, rendered_config, mode=0o600, overwrite=False):
    '''
    Given a target config filename and rendered config YAML, write it out to file. Create any
    containing directories as needed. But if the file already exists and overwrite is False,
    abort before writing anything.
    '''
    if not overwrite and os.path.exists(config_filename):
        raise FileExistsError(
            f'{config_filename} already exists. Aborting. Use --overwrite to replace the file.'
        )

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
        field_schema = borgmatic.config.schema.get_properties(schema['items']).get(field_name, {})
        description = field_schema.get('description')

        # No description to use? Skip it.
        if not field_schema or not description:
            return

        config[0].yaml_set_start_comment(description, indent=indent)

        # We only want the first key's description here, as the rest of the keys get commented by
        # add_comments_to_configuration_object().
        return


DEFAULT_KEYS = {'source_directories', 'repositories', 'keep_daily'}
COMMENTED_OUT_SENTINEL = 'COMMENT_OUT'


def add_comments_to_configuration_object(
    config, schema, source_config=None, indent=0, skip_first_field=False
):
    '''
    Using descriptions from a schema as a source, add those descriptions as comments to the given
    configuration dict, putting them before each field. Indent the comment the given number of
    characters.

    If skip_first_field is True, omit the comment for the initial field. This is useful for
    sequences, where the comment for the first field goes before the sequence itself.

    And a sentinel for commenting out options that are neither in DEFAULT_KEYS nor the the given
    source configuration dict. The idea is that any options used in the source configuration should
    stay active in the generated configuration.
    '''
    for index, field_name in enumerate(config.keys()):
        if skip_first_field and index == 0:
            continue

        field_schema = borgmatic.config.schema.get_properties(schema).get(field_name, {})
        description = field_schema.get('description', '').strip()

        # If this isn't a default key, add an indicator to the comment, flagging it to be commented
        # out from the sample configuration. This sentinel is consumed by downstream processing that
        # does the actual commenting out.
        if field_name not in DEFAULT_KEYS and (
            source_config is None or field_name not in source_config
        ):
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
            insert_newline_before_comment(config, field_name)


RUAMEL_YAML_COMMENTS_INDEX = 1


def merge_source_configuration_into_destination(destination_config, source_config):
    '''
    Deep merge the given source configuration dict into the destination configuration CommentedMap,
    favoring values from the source when there are collisions.

    The purpose of this is to upgrade configuration files from old versions of borgmatic by adding
    new configuration keys and comments.
    '''
    if not source_config:
        return destination_config
    if not destination_config or not isinstance(source_config, collections.abc.Mapping):
        return source_config

    for field_name, source_value in source_config.items():
        # This is a mapping. Recurse for this key/value.
        if isinstance(source_value, collections.abc.Mapping):
            destination_config[field_name] = merge_source_configuration_into_destination(
                destination_config[field_name], source_value
            )
            continue

        # This is a sequence. Recurse for each item in it.
        if isinstance(source_value, collections.abc.Sequence) and not isinstance(source_value, str):
            destination_value = destination_config[field_name]
            destination_config[field_name] = ruamel.yaml.comments.CommentedSeq(
                [
                    merge_source_configuration_into_destination(
                        destination_value[index] if index < len(destination_value) else None,
                        source_item,
                    )
                    for index, source_item in enumerate(source_value)
                ]
            )
            continue

        # This is some sort of scalar. Set it into the destination.
        destination_config[field_name] = source_config[field_name]

    return destination_config


def generate_sample_configuration(
    dry_run, source_filename, destination_filename, schema_filename, overwrite=False
):
    '''
    Given an optional source configuration filename, and a required destination configuration
    filename, the path to a schema filename in a YAML rendition of the JSON Schema format, and
    whether to overwrite a destination file, write out a sample configuration file based on that
    schema. If a source filename is provided, merge the parsed contents of that configuration into
    the generated configuration.
    '''
    schema = ruamel.yaml.YAML(typ='safe').load(open(schema_filename))
    source_config = None

    if source_filename:
        source_config = load.load_configuration(source_filename)
        normalize.normalize(source_filename, source_config)

        # The borgmatic.config.normalize.normalize() function tacks on an empty "bootstrap" if
        # needed, so the hook gets used by default. But we don't want it to end up in the generated
        # config unless the user has set it explicitly, as an empty "bootstrap:" won't validate.
        if source_config and source_config.get('bootstrap') == {}:
            del source_config['bootstrap']

    destination_config = merge_source_configuration_into_destination(
        schema_to_sample_configuration(schema, source_config), source_config
    )

    if dry_run:
        return

    write_configuration(
        destination_filename,
        comment_out_optional_configuration(render_configuration(destination_config)),
        overwrite=overwrite,
    )
