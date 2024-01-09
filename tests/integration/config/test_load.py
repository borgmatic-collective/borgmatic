import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.config import load as module


def test_load_configuration_parses_contents():
    builtins = flexmock(sys.modules['builtins'])
    config_file = io.StringIO('key: value')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {'key': 'value'}
    assert config_paths == {'config.yaml', 'other.yaml'}


def test_load_configuration_with_only_integer_value_does_not_raise():
    builtins = flexmock(sys.modules['builtins'])
    config_file = io.StringIO('33')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == 33
    assert config_paths == {'config.yaml', 'other.yaml'}


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
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {'key': 'value'}
    assert config_paths == {'config.yaml', '/tmp/include.yaml', 'other.yaml'}


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
    config_paths = {'other.yaml'}

    assert module.load_configuration('/etc/config.yaml', config_paths) == {'key': 'value'}
    assert config_paths == {'/etc/config.yaml', '/etc/include.yaml', 'other.yaml'}


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
    config_paths = set()

    with pytest.raises(FileNotFoundError):
        module.load_configuration('/etc/config.yaml', config_paths)


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
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {'key': 'value'}
    assert config_paths == {'config.yaml', '/root/include.yaml', 'other.yaml'}


def test_load_configuration_raises_if_absolute_include_does_not_exist():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(True)
    builtins.should_receive('open').with_args('/root/include.yaml').and_raise(FileNotFoundError)
    config_file = io.StringIO('key: !include /root/include.yaml')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(FileNotFoundError):
        assert module.load_configuration('config.yaml', config_paths)


def test_load_configuration_inlines_multiple_file_include_as_list():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(True)
    flexmock(module.os.path).should_receive('exists').never()
    include1_file = io.StringIO('value1')
    include1_file.name = '/root/include1.yaml'
    builtins.should_receive('open').with_args('/root/include1.yaml').and_return(include1_file)
    include2_file = io.StringIO('value2')
    include2_file.name = '/root/include2.yaml'
    builtins.should_receive('open').with_args('/root/include2.yaml').and_return(include2_file)
    config_file = io.StringIO('key: !include [/root/include1.yaml, /root/include2.yaml]')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {'key': ['value2', 'value1']}
    assert config_paths == {
        'config.yaml',
        '/root/include1.yaml',
        '/root/include2.yaml',
        'other.yaml',
    }


def test_load_configuration_include_with_unsupported_filename_type_raises():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(True)
    flexmock(module.os.path).should_receive('exists').never()
    config_file = io.StringIO('key: !include {path: /root/include.yaml}')
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(ValueError):
        module.load_configuration('config.yaml', config_paths)


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
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {
        'foo': 'override',
        'baz': 'quux',
    }
    assert config_paths == {'config.yaml', '/tmp/include.yaml', 'other.yaml'}


def test_load_configuration_merges_multiple_file_include():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include1_file = io.StringIO(
        '''
        foo: bar
        baz: quux
        original: yes
        '''
    )
    include1_file.name = 'include1.yaml'
    builtins.should_receive('open').with_args('/tmp/include1.yaml').and_return(include1_file)
    include2_file = io.StringIO(
        '''
        baz: second
        '''
    )
    include2_file.name = 'include2.yaml'
    builtins.should_receive('open').with_args('/tmp/include2.yaml').and_return(include2_file)
    config_file = io.StringIO(
        '''
        foo: override
        <<: !include [include1.yaml, include2.yaml]
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {
        'foo': 'override',
        'baz': 'second',
        'original': 'yes',
    }
    assert config_paths == {'config.yaml', '/tmp/include1.yaml', '/tmp/include2.yaml', 'other.yaml'}


def test_load_configuration_with_retain_tag_merges_include_but_keeps_local_values():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          foo: bar
          baz: quux

        other:
          a: b
          c: d
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff: !retain
          foo: override

        other:
          a: override
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {
        'stuff': {'foo': 'override'},
        'other': {'a': 'override', 'c': 'd'},
    }
    assert config_paths == {'config.yaml', '/tmp/include.yaml', 'other.yaml'}


def test_load_configuration_with_retain_tag_but_without_merge_include_raises():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff: !retain
          foo: bar
          baz: quux
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff:
          foo: override
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(ValueError):
        module.load_configuration('config.yaml', config_paths)


def test_load_configuration_with_retain_tag_on_scalar_raises():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          foo: bar
          baz: quux
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff:
          foo: !retain override
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(ValueError):
        module.load_configuration('config.yaml', config_paths)


def test_load_configuration_with_omit_tag_merges_include_and_omits_requested_values():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          - a
          - b
          - c
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff:
          - x
          - !omit b
          - y
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {'stuff': ['a', 'c', 'x', 'y']}
    assert config_paths == {'config.yaml', '/tmp/include.yaml', 'other.yaml'}


def test_load_configuration_with_omit_tag_on_unknown_value_merges_include_and_does_not_raise():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          - a
          - b
          - c
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff:
          - x
          - !omit q
          - y
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = {'other.yaml'}

    assert module.load_configuration('config.yaml', config_paths) == {
        'stuff': ['a', 'b', 'c', 'x', 'y']
    }
    assert config_paths == {'config.yaml', '/tmp/include.yaml', 'other.yaml'}


def test_load_configuration_with_omit_tag_on_non_list_item_raises():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          - a
          - b
          - c
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff: !omit
          - x
          - y
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(ValueError):
        module.load_configuration('config.yaml', config_paths)


def test_load_configuration_with_omit_tag_on_non_scalar_list_item_raises():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          - foo: bar
            baz: quux
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff:
          - !omit foo: bar
            baz: quux
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(ValueError):
        module.load_configuration('config.yaml', config_paths)


def test_load_configuration_with_omit_tag_but_without_merge_raises():
    builtins = flexmock(sys.modules['builtins'])
    flexmock(module.os).should_receive('getcwd').and_return('/tmp')
    flexmock(module.os.path).should_receive('isabs').and_return(False)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    include_file = io.StringIO(
        '''
        stuff:
          - a
          - !omit b
          - c
        '''
    )
    include_file.name = 'include.yaml'
    builtins.should_receive('open').with_args('/tmp/include.yaml').and_return(include_file)
    config_file = io.StringIO(
        '''
        stuff:
          - x
          - y
        <<: !include include.yaml
        '''
    )
    config_file.name = 'config.yaml'
    builtins.should_receive('open').with_args('config.yaml').and_return(config_file)
    config_paths = set()

    with pytest.raises(ValueError):
        module.load_configuration('config.yaml', config_paths)


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
    config_paths = set()

    with pytest.raises(module.ruamel.yaml.error.YAMLError):
        assert module.load_configuration('config.yaml', config_paths)


@pytest.mark.parametrize(
    'node_class',
    (
        module.ruamel.yaml.nodes.MappingNode,
        module.ruamel.yaml.nodes.SequenceNode,
        module.ruamel.yaml.nodes.ScalarNode,
    ),
)
def test_raise_retain_node_error_raises(node_class):
    with pytest.raises(ValueError):
        module.raise_retain_node_error(
            loader=flexmock(), node=node_class(tag=flexmock(), value=flexmock())
        )


def test_raise_omit_node_error_raises():
    with pytest.raises(ValueError):
        module.raise_omit_node_error(loader=flexmock(), node=flexmock())


def test_filter_omitted_nodes_discards_values_with_omit_tag_and_also_equal_values():
    nodes = [flexmock(), flexmock()]
    values = [
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='a'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='b'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='c'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='a'),
        module.ruamel.yaml.nodes.ScalarNode(tag='!omit', value='b'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='c'),
    ]

    result = module.filter_omitted_nodes(nodes, values)

    assert [item.value for item in result] == ['a', 'c', 'a', 'c']


def test_filter_omitted_nodes_keeps_all_values_when_given_only_one_node():
    nodes = [flexmock()]
    values = [
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='a'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='b'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='c'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='a'),
        module.ruamel.yaml.nodes.ScalarNode(tag='!omit', value='b'),
        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='c'),
    ]

    result = module.filter_omitted_nodes(nodes, values)

    assert [item.value for item in result] == ['a', 'b', 'c', 'a', 'b', 'c']


def test_merge_values_combines_mapping_values():
    nodes = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_hourly'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='24'
                        ),
                    ),
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='7'),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='25'
                        ),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_nanosecondly'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='1000'
                        ),
                    ),
                ],
            ),
        ),
    ]

    values = module.merge_values(nodes)

    assert len(values) == 4
    assert values[0][0].value == 'keep_hourly'
    assert values[0][1].value == '24'
    assert values[1][0].value == 'keep_daily'
    assert values[1][1].value == '7'
    assert values[2][0].value == 'keep_daily'
    assert values[2][1].value == '25'
    assert values[3][0].value == 'keep_nanosecondly'
    assert values[3][1].value == '1000'


def test_merge_values_combines_sequence_values():
    nodes = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
            module.ruamel.yaml.nodes.SequenceNode(
                tag='tag:yaml.org,2002:seq',
                value=[
                    module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='1'),
                    module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='2'),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
            module.ruamel.yaml.nodes.SequenceNode(
                tag='tag:yaml.org,2002:seq',
                value=[
                    module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='3'),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='option'),
            module.ruamel.yaml.nodes.SequenceNode(
                tag='tag:yaml.org,2002:seq',
                value=[
                    module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='4'),
                ],
            ),
        ),
    ]

    values = module.merge_values(nodes)

    assert len(values) == 4
    assert values[0].value == '1'
    assert values[1].value == '2'
    assert values[2].value == '3'
    assert values[3].value == '4'


def test_deep_merge_nodes_replaces_colliding_scalar_values():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_hourly'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='24'
                        ),
                    ),
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='7'),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='5'),
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
    assert options[0][0].value == 'keep_daily'
    assert options[0][1].value == '5'
    assert options[1][0].value == 'keep_hourly'
    assert options[1][1].value == '24'


def test_deep_merge_nodes_keeps_non_colliding_scalar_values():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_hourly'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='24'
                        ),
                    ),
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='7'),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_minutely'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='10'
                        ),
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
    assert options[0][0].value == 'keep_daily'
    assert options[0][1].value == '7'
    assert options[1][0].value == 'keep_hourly'
    assert options[1][1].value == '24'
    assert options[2][0].value == 'keep_minutely'
    assert options[2][1].value == '10'


def test_deep_merge_nodes_keeps_deeply_nested_values():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='storage'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='lock_wait'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='5'),
                    ),
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='extra_borg_options'
                        ),
                        module.ruamel.yaml.nodes.MappingNode(
                            tag='tag:yaml.org,2002:map',
                            value=[
                                (
                                    module.ruamel.yaml.nodes.ScalarNode(
                                        tag='tag:yaml.org,2002:str', value='init'
                                    ),
                                    module.ruamel.yaml.nodes.ScalarNode(
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
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='storage'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='extra_borg_options'
                        ),
                        module.ruamel.yaml.nodes.MappingNode(
                            tag='tag:yaml.org,2002:map',
                            value=[
                                (
                                    module.ruamel.yaml.nodes.ScalarNode(
                                        tag='tag:yaml.org,2002:str', value='prune'
                                    ),
                                    module.ruamel.yaml.nodes.ScalarNode(
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
    assert options[0][0].value == 'extra_borg_options'
    assert options[1][0].value == 'lock_wait'
    assert options[1][1].value == '5'
    nested_options = options[0][1].value
    assert len(nested_options) == 2
    assert nested_options[0][0].value == 'init'
    assert nested_options[0][1].value == '--init-option'
    assert nested_options[1][0].value == 'prune'
    assert nested_options[1][1].value == '--prune-option'


def test_deep_merge_nodes_appends_colliding_sequence_values():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:seq',
                            value=[
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 1'
                                ),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 2'
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:seq',
                            value=[
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 3'
                                ),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 4'
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
    assert section_key.value == 'hooks'
    options = section_value.value
    assert len(options) == 1
    assert options[0][0].value == 'before_backup'
    assert [item.value for item in options[0][1].value] == ['echo 1', 'echo 2', 'echo 3', 'echo 4']


def test_deep_merge_nodes_errors_on_colliding_values_of_different_types():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='echo oopsie daisy'
                        ),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:seq',
                            value=[
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 3'
                                ),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 4'
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
    ]

    with pytest.raises(ValueError):
        module.deep_merge_nodes(node_values)


def test_deep_merge_nodes_only_keeps_mapping_values_tagged_with_retain():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_hourly'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:int', value='24'
                        ),
                    ),
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='7'),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='retention'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='!retain',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='keep_daily'
                        ),
                        module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:int', value='5'),
                    ),
                ],
            ),
        ),
    ]

    result = module.deep_merge_nodes(node_values)
    assert len(result) == 1
    (section_key, section_value) = result[0]
    assert section_key.value == 'retention'
    assert section_value.tag == 'tag:yaml.org,2002:map'
    options = section_value.value
    assert len(options) == 1
    assert options[0][0].value == 'keep_daily'
    assert options[0][1].value == '5'


def test_deep_merge_nodes_only_keeps_sequence_values_tagged_with_retain():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:seq',
                            value=[
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 1'
                                ),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 2'
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='!retain',
                            value=[
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 3'
                                ),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 4'
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
    assert section_key.value == 'hooks'
    options = section_value.value
    assert len(options) == 1
    assert options[0][0].value == 'before_backup'
    assert options[0][1].tag == 'tag:yaml.org,2002:seq'
    assert [item.value for item in options[0][1].value] == ['echo 3', 'echo 4']


def test_deep_merge_nodes_skips_sequence_values_tagged_with_omit():
    node_values = [
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:seq',
                            value=[
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 1'
                                ),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 2'
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
        (
            module.ruamel.yaml.nodes.ScalarNode(tag='tag:yaml.org,2002:str', value='hooks'),
            module.ruamel.yaml.nodes.MappingNode(
                tag='tag:yaml.org,2002:map',
                value=[
                    (
                        module.ruamel.yaml.nodes.ScalarNode(
                            tag='tag:yaml.org,2002:str', value='before_backup'
                        ),
                        module.ruamel.yaml.nodes.SequenceNode(
                            tag='tag:yaml.org,2002:seq',
                            value=[
                                module.ruamel.yaml.ScalarNode(tag='!omit', value='echo 2'),
                                module.ruamel.yaml.ScalarNode(
                                    tag='tag:yaml.org,2002:str', value='echo 3'
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
    assert section_key.value == 'hooks'
    options = section_value.value
    assert len(options) == 1
    assert options[0][0].value == 'before_backup'
    assert [item.value for item in options[0][1].value] == ['echo 1', 'echo 3']
