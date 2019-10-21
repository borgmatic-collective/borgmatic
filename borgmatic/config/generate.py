import io
import os
import re

from ruamel import yaml

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
    for each section based on the schema "desc" description.
    '''
    example = schema.get('example')
    if example is not None:
        return example

    if 'seq' in schema:
        config = yaml.comments.CommentedSeq(
            [
                _schema_to_sample_configuration(item_schema, level, parent_is_sequence=True)
                for item_schema in schema['seq']
            ]
        )
        add_comments_to_configuration_sequence(
            config, schema, indent=(level * INDENT) + SEQUENCE_INDENT
        )
    elif 'map' in schema:
        config = yaml.comments.CommentedMap(
            [
                (section_name, _schema_to_sample_configuration(section_schema, level + 1))
                for section_name, section_schema in schema['map'].items()
            ]
        )
        indent = (level * INDENT) + (SEQUENCE_INDENT if parent_is_sequence else 0)
        add_comments_to_configuration_map(
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


REQUIRED_KEYS = {'source_directories', 'repositories', 'keep_daily'}
REQUIRED_SECTION_NAMES = {'location', 'retention'}


def _comment_out_optional_configuration(rendered_config):
    '''
    Post-process a rendered configuration string to comment out optional key/values. The idea is
    that this prevents the user from having to comment out a bunch of configuration they don't care
    about to get to a minimal viable configuration file.

    Ideally ruamel.yaml would support this during configuration generation, but it's not terribly
    easy to accomplish that way.
    '''
    lines = []
    required = False

    for line in rendered_config.split('\n'):
        key = line.strip().split(':')[0]

        if key in REQUIRED_SECTION_NAMES:
            lines.append(line)
            continue

        # Upon encountering a required configuration option, skip commenting out lines until the
        # next blank line.
        if key in REQUIRED_KEYS:
            required = True
        elif not key:
            required = False

        lines.append(_comment_out_line(line) if not required else line)

    return '\n'.join(lines)


def _render_configuration(config):
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
    If the given config sequence's items are maps, then mine the schema for the description of the
    map's first item, and slap that atop the sequence. Indent the comment the given number of
    characters.

    Doing this for sequences of maps results in nice comments that look like:

    ```
    things:
          # First key description. Added by this function.
        - key: foo
          # Second key description. Added by add_comments_to_configuration_map().
          other: bar
    ```
    '''
    if 'map' not in schema['seq'][0]:
        return

    for field_name in config[0].keys():
        field_schema = schema['seq'][0]['map'].get(field_name, {})
        description = field_schema.get('desc')

        # No description to use? Skip it.
        if not field_schema or not description:
            return

        config[0].yaml_set_start_comment(description, indent=indent)

        # We only want the first key's description here, as the rest of the keys get commented by
        # add_comments_to_configuration_map().
        return


def add_comments_to_configuration_map(config, schema, indent=0, skip_first=False):
    '''
    Using descriptions from a schema as a source, add those descriptions as comments to the given
    config mapping, before each field. Indent the comment the given number of characters.
    '''
    for index, field_name in enumerate(config.keys()):
        if skip_first and index == 0:
            continue

        field_schema = schema['map'].get(field_name, {})
        description = field_schema.get('desc')

        # No description to use? Skip it.
        if not field_schema or not description:
            continue

        config.yaml_set_comment_before_after_key(key=field_name, before=description, indent=indent)

        if index > 0:
            _insert_newline_before_comment(config, field_name)


def generate_sample_configuration(config_filename, schema_filename):
    '''
    Given a target config filename and the path to a schema filename in pykwalify YAML schema
    format, write out a sample configuration file based on that schema.
    '''
    schema = yaml.round_trip_load(open(schema_filename))
    config = _schema_to_sample_configuration(schema)

    write_configuration(
        config_filename, _comment_out_optional_configuration(_render_configuration(config))
    )
