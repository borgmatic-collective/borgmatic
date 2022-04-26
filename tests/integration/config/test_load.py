import sys

import pytest
import ruamel.yaml
from flexmock import flexmock

from borgmatic.config import load as module


def test_load_configuration_parses_contents():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('config.yaml').and_return('key: value')

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_inlines_include():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('include.yaml').and_return('value')
    builtins.should_receive('open').with_args('config.yaml').and_return(
        'key: !include include.yaml'
    )

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_merges_include():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('include.yaml').and_return(
        '''
        foo: bar
        baz: quux
        '''
    )
    builtins.should_receive('open').with_args('config.yaml').and_return(
        '''
        foo: override
        <<: !include include.yaml
        '''
    )

    assert module.load_configuration('config.yaml') == {'foo': 'override', 'baz': 'quux'}


def test_load_configuration_does_not_merge_include_list():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('include.yaml').and_return(
        '''
          - one
          - two
        '''
    )
    builtins.should_receive('open').with_args('config.yaml').and_return(
        '''
        foo: bar
        repositories:
          <<: !include include.yaml
        '''
    )

    with pytest.raises(ruamel.yaml.error.YAMLError):
        assert module.load_configuration('config.yaml')


def test_deep_merge_nodes_replaces_colliding_scalar_values():
    node_values = [
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_hourly'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='24'),
                    ),
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='7'),
                    ),
                ],
            ),
        ),
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='5'),
                    ),
                ],
            ),
        ),
    ]

    result = module.deep_merge_nodes(node_values)
    assert len(result) == 1
    (section_key, section_value) = result[0]
    assert section_key.value == 'retention'
    options = section_value.value
    assert len(options) == 2
    assert options[0][0].value == 'keep_hourly'
    assert options[0][1].value == '24'
    assert options[1][0].value == 'keep_daily'
    assert options[1][1].value == '5'


def test_deep_merge_nodes_keeps_non_colliding_scalar_values():
    node_values = [
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_hourly'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='24'),
                    ),
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='7'),
                    ),
                ],
            ),
        ),
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_minutely'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='10'),
                    ),
                ],
            ),
        ),
    ]

    result = module.deep_merge_nodes(node_values)
    assert len(result) == 1
    (section_key, section_value) = result[0]
    assert section_key.value == 'retention'
    options = section_value.value
    assert len(options) == 3
    assert options[0][0].value == 'keep_hourly'
    assert options[0][1].value == '24'
    assert options[1][0].value == 'keep_daily'
    assert options[1][1].value == '7'
    assert options[2][0].value == 'keep_minutely'
    assert options[2][1].value == '10'


def test_deep_merge_nodes_keeps_deeply_nested_values():
    node_values = [
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='storage'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='lock_wait'
                        ),
                        ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='5'),
                    ),
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='extra_borg_options'
                        ),
                        ruamel.yaml.nodes.MappingNode(
                            tag='tag:yaml.org,2002:map',
                            value=[
                                (
                                    ruamel.yaml.nodes.ScalarNode(
                                        tag='tag:yaml.org,2002:str', value='init'
                                    ),
                                    ruamel.yaml.nodes.ScalarNode(
                                        tag='tag:yaml.org,2002:str', value='--init-option'
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='storage'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='extra_borg_options'
                        ),
                        ruamel.yaml.nodes.MappingNode(
                            tag='tag:yaml.org,2002:map',
                            value=[
                                (
                                    ruamel.yaml.nodes.ScalarNode(
                                        tag='tag:yaml.org,2002:str', value='prune'
                                    ),
                                    ruamel.yaml.nodes.ScalarNode(
                                        tag='tag:yaml.org,2002:str', value='--prune-option'
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
    ]

    result = module.deep_merge_nodes(node_values)
    assert len(result) == 1
    (section_key, section_value) = result[0]
    assert section_key.value == 'storage'
    options = section_value.value
    assert len(options) == 2
    assert options[0][0].value == 'lock_wait'
    assert options[0][1].value == '5'
    assert options[1][0].value == 'extra_borg_options'
    nested_options = options[1][1].value
    assert len(nested_options) == 2
    assert nested_options[0][0].value == 'init'
    assert nested_options[0][1].value == '--init-option'
    assert nested_options[1][0].value == 'prune'
    assert nested_options[1][1].value == '--prune-option'
