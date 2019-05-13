import os

from ruamel import yaml

INDENT = 4


def _insert_newline_before_comment(config, field_name):
    '''
    Using some ruamel.yaml black magic, insert a blank line in the config right before the given
    field and its comments.
    '''
    config.ca.items[field_name][1].insert(
        0, yaml.tokens.CommentToken('\n', yaml.error.CommentMark(0), None)
    )


def _schema_to_sample_configuration(schema, level=0):
    '''
    Given a loaded configuration schema, generate and return sample config for it. Include comments
    for each section based on the schema "desc" description.
    '''
    example = schema.get('example')
    if example is not None:
        return example

    config = yaml.comments.CommentedMap(
        [
            (section_name, _schema_to_sample_configuration(section_schema, level + 1))
            for section_name, section_schema in schema['map'].items()
        ]
    )

    add_comments_to_configuration(config, schema, indent=(level * INDENT))

    return config


def _comment_out_line(line):
    # If it's already is commented out (or empty), there's nothing further to do!
    stripped_line = line.lstrip()
    if not stripped_line or stripped_line.startswith('#'):
        return line

    # Comment out the names of optional sections.
    one_indent = ' ' * INDENT
    if not line.startswith(one_indent):
        return '#' + line

    # Otherwise, comment out the line, but insert the "#" after the first indent for aesthetics.
    return '#'.join((one_indent, line[INDENT:]))


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
    return yaml.round_trip_dump(config, indent=INDENT, block_seq_indent=INDENT)


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
