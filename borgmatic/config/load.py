import os

import ruamel.yaml

from borgmatic.logger import get_logger

logger = get_logger(__name__)


def load_configuration(filename):
    '''
    Load the given configuration file and return its contents as a data structure of nested dicts
    and lists.

    Raise ruamel.yaml.error.YAMLError if something goes wrong parsing the YAML, or RecursionError
    if there are too many recursive includes.
    '''
    yaml = ruamel.yaml.YAML(typ='safe')
    yaml.Constructor = Include_constructor

    return yaml.load(open(filename))


def include_configuration(loader, filename_node):
    '''
    Load the given YAML filename (ignoring the given loader so we can use our own), and return its
    contents as a data structure of nested dicts and lists.
    '''
    return load_configuration(os.path.expanduser(filename_node.value))


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
        Support the special case of shallow merging included configuration into an existing mapping
        using the YAML '<<' merge key. Example syntax:

        ```
        retention:
            keep_daily: 1
            <<: !include common.yaml
        ```
        '''
        representer = ruamel.yaml.representer.SafeRepresenter()

        for index, (key_node, value_node) in enumerate(node.value):
            if key_node.tag == u'tag:yaml.org,2002:merge' and value_node.tag == '!include':
                included_value = representer.represent_mapping(
                    tag='tag:yaml.org,2002:map', mapping=self.construct_object(value_node)
                )
                node.value[index] = (key_node, included_value)

        super(Include_constructor, self).flatten_mapping(node)
