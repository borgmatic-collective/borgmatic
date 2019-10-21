from collections import OrderedDict

import pytest
from flexmock import flexmock

from borgmatic.config import generate as module


def test_schema_to_sample_configuration_generates_config_map_with_examples():
    flexmock(module.yaml.comments).should_receive('CommentedMap').replace_with(OrderedDict)
    flexmock(module).should_receive('add_comments_to_configuration_map')
    schema = {
        'map': OrderedDict(
            [
                ('section1', {'map': {'field1': OrderedDict([('example', 'Example 1')])}}),
                (
                    'section2',
                    {
                        'map': OrderedDict(
                            [
                                ('field2', {'example': 'Example 2'}),
                                ('field3', {'example': 'Example 3'}),
                            ]
                        )
                    },
                ),
            ]
        )
    }

    config = module._schema_to_sample_configuration(schema)

    assert config == OrderedDict(
        [
            ('section1', OrderedDict([('field1', 'Example 1')])),
            ('section2', OrderedDict([('field2', 'Example 2'), ('field3', 'Example 3')])),
        ]
    )


def test_schema_to_sample_configuration_generates_config_sequence_of_strings_with_example():
    flexmock(module.yaml.comments).should_receive('CommentedSeq').replace_with(list)
    flexmock(module).should_receive('add_comments_to_configuration_sequence')
    schema = {'seq': [{'type': 'str'}], 'example': ['hi']}

    config = module._schema_to_sample_configuration(schema)

    assert config == ['hi']


def test_schema_to_sample_configuration_generates_config_sequence_of_maps_with_examples():
    flexmock(module.yaml.comments).should_receive('CommentedSeq').replace_with(list)
    flexmock(module).should_receive('add_comments_to_configuration_sequence')
    schema = {
        'seq': [
            {
                'map': OrderedDict(
                    [('field1', {'example': 'Example 1'}), ('field2', {'example': 'Example 2'})]
                )
            }
        ]
    }

    config = module._schema_to_sample_configuration(schema)

    assert config == [OrderedDict([('field1', 'Example 1'), ('field2', 'Example 2')])]


def test_schema_to_sample_configuration_with_unsupported_schema_raises():
    schema = {'gobbledygook': [{'type': 'not-your'}]}

    with pytest.raises(ValueError):
        module._schema_to_sample_configuration(schema)
