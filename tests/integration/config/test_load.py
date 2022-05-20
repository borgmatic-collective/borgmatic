import io
import sys

import pytest
import ruamel.yaml
from flexmock import flexmock

from borgmatic.config import load as module


def test_load_configuration_parses_contents():
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args('config.yaml').and_return('key: value')

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_inlines_include_relative_to_current_directory():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO('value')
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO('key: !include include.yaml')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_inlines_include_relative_to_config_parent_directory():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').with_args('/etc').and_return(True)
    flexmock(module.os.path).should_receive('isabs').with_args('/etc/config.yaml').and_return(True)
    flexmock(module.os.path).should_receive('isabs').with_args('include.yaml').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/tmp/include.yaml').and_return(
        False
    )
    flexmock(module.os.path).should_receive('exists').with_args('/etc/include.yaml').and_return(
        True
    )
    include_file = io.StringIO('value')
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/etc/include.yaml').and_return(include_file)
    config_file = io.StringIO('key: !include include.yaml')
    config_file.name = '/etc/config.yaml'
    builtins.should_receive('open').with_args('/etc/config.yaml').and_return(config_file)

    assert module.load_configuration('/etc/config.yaml') == {'key': 'value'}


def test_load_configuration_raises_if_relative_include_does_not_exist():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').with_args('/etc').and_return(True)
    flexmock(module.os.path).should_receive('isabs').with_args('/etc/config.yaml').and_return(True)
    flexmock(module.os.path).should_receive('isabs').with_args('include.yaml').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(False)
    config_file = io.StringIO('key: !include include.yaml')
    config_file.name = '/etc/config.yaml'
    builtins.should_receive('open').with_args('/etc/config.yaml').and_return(config_file)

    with pytest.raises(FileNotFoundError):
        module.load_configuration('/etc/config.yaml')


def test_load_configuration_inlines_absolute_include():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(True)
    flexmock(module.os.path).should_receive('exists').never()
    include_file = io.StringIO('value')
    include_file.name = '/root/include.yaml'
    builtins.should_receive('open').with_args('/root/include.yaml').and_return(include_file)
    config_file = io.StringIO('key: !include /root/include.yaml')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)

    assert module.load_configuration('config.yaml') == {'key': 'value'}


def test_load_configuration_raises_if_absolute_include_does_not_exist():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(True)
    builtins.should_receive('open').with_args('/root/include.yaml').and_raise(FileNotFoundError)
    config_file = io.StringIO('key: !include /root/include.yaml')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)

    with pytest.raises(FileNotFoundError):
        assert module.load_configuration('config.yaml')


def test_load_configuration_merges_include():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        foo: bar
        baz: quux
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        foo: override
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)

    assert module.load_configuration('config.yaml') == {'foo': 'override', 'baz': 'quux'}


def test_load_configuration_does_not_merge_include_list():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
          - one
          - two
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        foo: bar
        repositories:
          <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)

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


def test_deep_merge_nodes_appends_colliding_sequence_values():
    node_values = [
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:int', value=['echo 1', 'echo 2']
                        ),
                    ),
                ],
            ),
        ),
        (
            ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:int', value=['echo 3', 'echo 4']
                        ),
                    ),
                ],
            ),
        ),
    ]

    result = module.deep_merge_nodes(node_values)
    assert len(result) == 1
    (section_key, section_value) = result[0]
    assert section_key.value == 'hooks'
    options = section_value.value
    assert len(options) == 1
    assert options[0][0].value == 'before_backup'
    assert options[0][1].value == ['echo 1', 'echo 2', 'echo 3', 'echo 4']
