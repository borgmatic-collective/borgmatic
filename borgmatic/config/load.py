import functools
import itertools
import logging
import operator
import os

import ruamel.yaml

logger = logging.getLogger(__name__)


def probe_and_include_file(filename, include_directories, config_paths):
    '''
    Given a filename to include, a list of include directories to search for matching files, and a
    set of configuration paths, probe for the file, load it, and return the loaded configuration as
    a data structure of nested dicts, lists, etc. Add the filename to the given configuration paths.

    Raise FileNotFoundError if the included file was not found.
    '''
    expanded_filename = os.path.expanduser(filename)

    if os.path.isabs(expanded_filename):
        return load_configuration(expanded_filename, config_paths)

    candidate_filenames = {
        os.path.join(directory, expanded_filename) for directory in include_directories
    }

    for candidate_filename in candidate_filenames:
        if os.path.exists(candidate_filename):
            return load_configuration(candidate_filename, config_paths)

    raise FileNotFoundError(
        f'Could not find include {filename} at {" or ".join(candidate_filenames)}'
    )


def include_configuration(loader, filename_node, include_directory, config_paths):
    '''
    Given a ruamel.yaml.loader.Loader, a ruamel.yaml.nodes.ScalarNode containing the included
    filename (or a list containing multiple such filenames), an include directory path to search for
    matching files, and a set of configuration paths, load the given YAML filenames (ignoring the
    given loader so we can use our own) and return their contents as data structure of nested dicts,
    lists, etc. Add the names of included files to the given configuration paths. If the given
    filename node's value is a scalar string, then the return value will be a single value. But if
    the given node value is a list, then the return value will be a list of values, one per loaded
    configuration file.

    If a filename is relative, probe for it within: 1. the current working directory and 2. the
    given include directory.

    Raise FileNotFoundError if an included file was not found.
    '''
    include_directories = [os.getcwd(), os.path.abspath(include_directory)]

    if isinstance(filename_node.value, str):
        return probe_and_include_file(filename_node.value, include_directories, config_paths)

    if (
        isinstance(filename_node.value, list)
        and len(filename_node.value)
        and isinstance(filename_node.value[0], ruamel.yaml.nodes.ScalarNode)
    ):
        # Reversing the values ensures the correct ordering if these includes are subsequently
        # merged together.
        return [
            probe_and_include_file(node.value, include_directories, config_paths)
            for node in reversed(filename_node.value)
        ]

    raise ValueError(
        'The value given for the !include tag is invalid; use a single filename or a list of filenames instead'
    )


def raise_retain_node_error(loader, node):
    '''
    Given a ruamel.yaml.loader.Loader and a YAML node, raise an error about "!retain" usage.

    Raise ValueError if a mapping or sequence node is given, as that indicates that "!retain" was
    used in a configuration file without a merge. In configuration files with a merge, mapping and
    sequence nodes with "!retain" tags are handled by deep_merge_nodes() below.

    Also raise ValueError if a scalar node is given, as "!retain" is not supported on scalar nodes.
    '''
    if isinstance(node, (ruamel.yaml.nodes.MappingNode, ruamel.yaml.nodes.SequenceNode)):
        raise ValueError(
            'The !retain tag may only be used within a configuration file containing a merged !include tag.'
        )

    raise ValueError('The !retain tag may only be used on a mapping or list.')


def raise_omit_node_error(loader, node):
    '''
    Given a ruamel.yaml.loader.Loader and a YAML node, raise an error about "!omit" usage.

    Raise ValueError unconditionally, as an "!omit" node here indicates it was used in a
    configuration file without a merge. In configuration files with a merge, nodes with "!omit"
    tags are handled by deep_merge_nodes() below.
    '''
    raise ValueError(
        'The !omit tag may only be used on a scalar (e.g., string) or list element within a configuration file containing a merged !include tag.'
    )


class Include_constructor(ruamel.yaml.SafeConstructor):
    '''
    A YAML "constructor" (a ruamel.yaml concept) that supports a custom "!include" tag for including
    separate YAML configuration files. Example syntax: `option: !include common.yaml`
    '''

    def __init__(
        self, preserve_quotes=None, loader=None, include_directory=None, config_paths=None
    ):
        super(Include_constructor, self).__init__(preserve_quotes, loader)
        self.add_constructor(
            '!include',
            functools.partial(
                include_configuration,
                include_directory=include_directory,
                config_paths=config_paths,
            ),
        )

        # These are catch-all error handlers for tags that don't get applied and removed by
        # deep_merge_nodes() below.
        self.add_constructor('!retain', raise_retain_node_error)
        self.add_constructor('!omit', raise_omit_node_error)

    def flatten_mapping(self, node):
        '''
        Support the special case of deep merging included configuration into an existing mapping
        using the YAML '<<' merge key. Example syntax:

        ```
        option:
            sub_option: 1

        <<: !include common.yaml
        ```

        These includes are deep merged into the current configuration file. For instance, in this
        example, any "option" with sub-options in common.yaml will get merged into the corresponding
        "option" with sub-options in the example configuration file.
        '''
        representer = ruamel.yaml.representer.SafeRepresenter()

        for index, (key_node, value_node) in enumerate(node.value):
            if key_node.tag == u'tag:yaml.org,2002:merge' and value_node.tag == '!include':
                # Replace the merge include with a sequence of included configuration nodes ready
                # for merging. The construct_object() call here triggers include_configuration()
                # among other constructors.
                node.value[index] = (
                    key_node,
                    representer.represent_data(self.construct_object(value_node)),
                )

        # This super().flatten_mapping() call actually performs "<<" merges.
        super(Include_constructor, self).flatten_mapping(node)

        node.value = deep_merge_nodes(node.value)


def load_configuration(filename, config_paths=None):
    '''
    Load the given configuration file and return its contents as a data structure of nested dicts
    and lists. Add the filename to the given configuration paths set, and also add any included
    configuration filenames.

    Raise ruamel.yaml.error.YAMLError if something goes wrong parsing the YAML, or RecursionError
    if there are too many recursive includes.
    '''
    if config_paths is None:
        config_paths = set()

    # Use an embedded derived class for the include constructor so as to capture the include
    # directory and configuration paths values. (functools.partial doesn't work for this use case
    # because yaml.Constructor has to be an actual class.)
    class Include_constructor_with_extras(Include_constructor):
        def __init__(self, preserve_quotes=None, loader=None):
            super(Include_constructor_with_extras, self).__init__(
                preserve_quotes,
                loader,
                include_directory=os.path.dirname(filename),
                config_paths=config_paths,
            )

    yaml = ruamel.yaml.YAML(typ='safe')
    yaml.Constructor = Include_constructor_with_extras
    config_paths.add(filename)

    with open(filename) as file:
        return yaml.load(file.read())


def filter_omitted_nodes(nodes, values):
    '''
    Given a nested borgmatic configuration data structure as a list of tuples in the form of:

    [
        (
            ruamel.yaml.nodes.ScalarNode as a key,
            ruamel.yaml.nodes.MappingNode or other Node as a value,
        ),
        ...
    ]

    ... and a combined list of all values for those nodes, return a filtered list of the values,
    omitting any that have an "!omit" tag (or with a value matching such nodes).

    But if only a single node is given, bail and return the given values unfiltered, as "!omit" only
    applies when there are merge includes (and therefore multiple nodes).
    '''
    if len(nodes) <= 1:
        return values

    omitted_values = tuple(node.value for node in values if node.tag == '!omit')

    return [node for node in values if node.value not in omitted_values]


def merge_values(nodes):
    '''
    Given a nested borgmatic configuration data structure as a list of tuples in the form of:

    [
        (
            ruamel.yaml.nodes.ScalarNode as a key,
            ruamel.yaml.nodes.MappingNode or other Node as a value,
        ),
        ...
    ]

    ... merge its sequence or mapping node values and return the result. For sequence nodes, this
    means appending together its contained lists. For mapping nodes, it means merging its contained
    dicts.
    '''
    return functools.reduce(operator.add, (value.value for key, value in nodes))


def deep_merge_nodes(nodes):
    '''
    Given a nested borgmatic configuration data structure as a list of tuples in the form of:

    [
        (
            ruamel.yaml.nodes.ScalarNode as a key,
            ruamel.yaml.nodes.MappingNode or other Node as a value,
        ),
        ...
    ]

    ... deep merge any node values corresponding to duplicate keys and return the result. The
    purpose of merging like this is to support, for instance, merging one borgmatic configuration
    file into another for reuse, such that a configuration option with sub-options does not
    completely replace the corresponding option in a merged file.

    If there are colliding keys with scalar values (e.g., integers or strings), the last of the
    values wins.

    For instance, given node values of:

        [
            (
                ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
                MappingNode(tag='tag:yaml.org,2002:map', value=[
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='sub_option1'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='1')
                    ),
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='sub_option2'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='2')
                    ),
                ]),
            ),
            (
                ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
                MappingNode(tag='tag:yaml.org,2002:map', value=[
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='sub_option2'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='5')
                    ),
                ]),
            ),
        ]

    ... the returned result would be:

        [
            (
                ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
                MappingNode(tag='tag:yaml.org,2002:map', value=[
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='sub_option1'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='1')
                    ),
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='sub_option2'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='5')
                    ),
                ]),
            ),
        ]

    This function supports multi-way merging, meaning that if the same option name exists three or
    more times (at the same scope level), all of those instances get merged together.

    If a mapping or sequence node has a YAML "!retain" tag, then that node is not merged.

    Raise ValueError if a merge is implied using multiple incompatible types.
    '''
    merged_nodes = []

    def get_node_key_name(node):
        return node[0].value

    # Bucket the nodes by their keys. Then merge all of the values sharing the same key.
    for key_name, grouped_nodes in itertools.groupby(
        sorted(nodes, key=get_node_key_name), get_node_key_name
    ):
        grouped_nodes = list(grouped_nodes)

        # The merged node inherits its attributes from the final node in the group.
        (last_node_key, last_node_value) = grouped_nodes[-1]
        value_types = set(type(value) for (_, value) in grouped_nodes)

        if len(value_types) > 1:
            raise ValueError(
                f'Incompatible types found when trying to merge "{key_name}:" values across configuration files: {", ".join(value_type.id for value_type in value_types)}'
            )

        # If we're dealing with MappingNodes, recurse and merge its values as well.
        if ruamel.yaml.nodes.MappingNode in value_types:
            # A "!retain" tag says to skip deep merging for this node. Replace the tag so
            # downstream schema validation doesn't break on our application-specific tag.
            if last_node_value.tag == '!retain' and len(grouped_nodes) > 1:
                last_node_value.tag = 'tag:yaml.org,2002:map'
                merged_nodes.append((last_node_key, last_node_value))
            else:
                merged_nodes.append(
                    (
                        last_node_key,
                        ruamel.yaml.nodes.MappingNode(
                            tag=last_node_value.tag,
                            value=deep_merge_nodes(merge_values(grouped_nodes)),
                            start_mark=last_node_value.start_mark,
                            end_mark=last_node_value.end_mark,
                            flow_style=last_node_value.flow_style,
                            comment=last_node_value.comment,
                            anchor=last_node_value.anchor,
                        ),
                    )
                )

            continue

        # If we're dealing with SequenceNodes, merge by appending sequences together.
        if ruamel.yaml.nodes.SequenceNode in value_types:
            if last_node_value.tag == '!retain' and len(grouped_nodes) > 1:
                last_node_value.tag = 'tag:yaml.org,2002:seq'
                merged_nodes.append((last_node_key, last_node_value))
            else:
                merged_nodes.append(
                    (
                        last_node_key,
                        ruamel.yaml.nodes.SequenceNode(
                            tag=last_node_value.tag,
                            value=filter_omitted_nodes(grouped_nodes, merge_values(grouped_nodes)),
                            start_mark=last_node_value.start_mark,
                            end_mark=last_node_value.end_mark,
                            flow_style=last_node_value.flow_style,
                            comment=last_node_value.comment,
                            anchor=last_node_value.anchor,
                        ),
                    )
                )

            continue

        merged_nodes.append((last_node_key, last_node_value))

    return merged_nodes
