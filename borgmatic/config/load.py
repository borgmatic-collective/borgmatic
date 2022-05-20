import logging
import os

import ruamel.yaml

logger = logging.getLogger(__name__)


class Yaml_with_loader_stream(ruamel.yaml.YAML):
    '''
    A derived class of ruamel.yaml.YAML that simply tacks the loaded stream (file object) onto the
    loader class so that it's available anywhere that's passed a loader (in this case,
    include_configuration() below).
    '''

    def get_constructor_parser(self, stream):
        constructor, parser = super(Yaml_with_loader_stream, self).get_constructor_parser(stream)
        constructor.loader.stream = stream
        return constructor, parser


def load_configuration(filename):
    '''
    Load the given configuration file and return its contents as a data structure of nested dicts
    and lists.

    Raise ruamel.yaml.error.YAMLError if something goes wrong parsing the YAML, or RecursionError
    if there are too many recursive includes.
    '''
    yaml = Yaml_with_loader_stream(typ='safe')
    yaml.Constructor = Include_constructor

    return yaml.load(open(filename))


def include_configuration(loader, filename_node):
    '''
    Load the given YAML filename (ignoring the given loader so we can use our own) and return its
    contents as a data structure of nested dicts and lists. If the filename is relative, probe for
    it within 1. the current working directory and 2. the directory containing the YAML file doing
    the including.

    Raise FileNotFoundError if an included file was not found.
    '''
    include_directories = [os.getcwd(), os.path.abspath(os.path.dirname(loader.stream.name))]
    include_filename = os.path.expanduser(filename_node.value)

    if not os.path.isabs(include_filename):
        candidate_filenames = [
            os.path.join(directory, include_filename) for directory in include_directories
        ]

        for candidate_filename in candidate_filenames:
            if os.path.exists(candidate_filename):
                include_filename = candidate_filename
                break
        else:
            raise FileNotFoundError(
                f'Could not find include {filename_node.value} at {" or ".join(candidate_filenames)}'
            )

    return load_configuration(include_filename)


DELETED_NODE = object()


def deep_merge_nodes(nodes):
    '''
    Given a nested borgmatic configuration data structure as a list of tuples in the form of:

        (
            ruamel.yaml.nodes.ScalarNode as a key,
            ruamel.yaml.nodes.MappingNode or other Node as a value,
        ),

    ... deep merge any node values corresponding to duplicate keys and return the result. If
    there are colliding keys with non-MappingNode values (e.g., integers or strings), the last
    of the values wins.

    For instance, given node values of:

        [
            (
                ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
                MappingNode(tag='tag:yaml.org,2002:map', value=[
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='keep_hourly'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='24')
                    ),
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='keep_daily'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='7')
                    ),
                ]),
            ),
            (
                ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
                MappingNode(tag='tag:yaml.org,2002:map', value=[
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='keep_daily'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='5')
                    ),
                ]),
            ),
        ]

    ... the returned result would be:

        [
            (
                ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
                MappingNode(tag='tag:yaml.org,2002:map', value=[
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='keep_hourly'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='24')
                    ),
                    (
                        ScalarNode(tag='tag:yaml.org,2002:str', value='keep_daily'),
                        ScalarNode(tag='tag:yaml.org,2002:int', value='5')
                    ),
                ]),
            ),
        ]

    The purpose of deep merging like this is to support, for instance, merging one borgmatic
    configuration file into another for reuse, such that a configuration section ("retention",
    etc.) does not completely replace the corresponding section in a merged file.
    '''
    # Map from original node key/value to the replacement merged node. DELETED_NODE as a replacement
    # node indications deletion.
    replaced_nodes = {}

    # To find nodes that require merging, compare each node with each other node.
    for a_key, a_value in nodes:
        for b_key, b_value in nodes:
            # If we've already considered one of the nodes for merging, skip it.
            if (a_key, a_value) in replaced_nodes or (b_key, b_value) in replaced_nodes:
                continue

            # If the keys match and the values are different, we need to merge these two A and B nodes.
            if a_key.tag == b_key.tag and a_key.value == b_key.value and a_value != b_value:
                # Since we're merging into the B node, consider the A node a duplicate and remove it.
                replaced_nodes[(a_key, a_value)] = DELETED_NODE

                # If we're dealing with MappingNodes, recurse and merge its values as well.
                if isinstance(b_value, ruamel.yaml.nodes.MappingNode):
                    replaced_nodes[(b_key, b_value)] = (
                        b_key,
                        ruamel.yaml.nodes.MappingNode(
                            tag=b_value.tag,
                            value=deep_merge_nodes(a_value.value + b_value.value),
                            start_mark=b_value.start_mark,
                            end_mark=b_value.end_mark,
                            flow_style=b_value.flow_style,
                            comment=b_value.comment,
                            anchor=b_value.anchor,
                        ),
                    )
                # If we're dealing with SequenceNodes, merge by appending one sequence to the other.
                elif isinstance(b_value, ruamel.yaml.nodes.SequenceNode):
                    replaced_nodes[(b_key, b_value)] = (
                        b_key,
                        ruamel.yaml.nodes.SequenceNode(
                            tag=b_value.tag,
                            value=a_value.value + b_value.value,
                            start_mark=b_value.start_mark,
                            end_mark=b_value.end_mark,
                            flow_style=b_value.flow_style,
                            comment=b_value.comment,
                            anchor=b_value.anchor,
                        ),
                    )

    return [
        replaced_nodes.get(node, node) for node in nodes if replaced_nodes.get(node) != DELETED_NODE
    ]


class Include_constructor(ruamel.yaml.SafeConstructor):
    '''
    A YAML "constructor" (a ruamel.yaml concept) that supports a custom "!include" tag for including
    separate YAML configuration files. Example syntax: `retention: !include common.yaml`
    '''

    def __init__(self, preserve_quotes=None, loader=None):
        super(Include_constructor, self).__init__(preserve_quotes, loader)
        self.add_constructor('!include', include_configuration)

    def flatten_mapping(self, node):
        '''
        Support the special case of deep merging included configuration into an existing mapping
        using the YAML '<<' merge key. Example syntax:

        ```
        retention:
            keep_daily: 1

        <<: !include common.yaml
        ```

        These includes are deep merged into the current configuration file. For instance, in this
        example, any "retention" options in common.yaml will get merged into the "retention" section
        in the example configuration file.
        '''
        representer = ruamel.yaml.representer.SafeRepresenter()

        for index, (key_node, value_node) in enumerate(node.value):
            if key_node.tag == u'tag:yaml.org,2002:merge' and value_node.tag == '!include':
                included_value = representer.represent_data(self.construct_object(value_node))
                node.value[index] = (key_node, included_value)

        super(Include_constructor, self).flatten_mapping(node)

        node.value = deep_merge_nodes(node.value)
