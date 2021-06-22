from collections import OrderedDict

import pytest
from flexmock import flexmock

from borgmatic.config import generate as module


def test_schema_to_sample_configuration_generates_config_map_with_examples():
    flexmock(module.yaml.comments).should_receive('CommentedMap').replace_with(OrderedDict)
    flexmock(module).should_receive('add_comments_to_configuration_object')
    schema = {
        'type': 'object',
        'properties': OrderedDict(
            [
                (
                    'section1',
                    {
                        'type': 'object',
                        'properties': {'field1': OrderedDict([('example', 'Example 1')])},
                    },
                ),
                (
                    'section2',
                    {
                        'type': 'object',
                        'properties': OrderedDict(
                            [
                                ('field2', {'example': 'Example 2'}),
                                ('field3', {'example': 'Example 3'}),
                            ]
                        ),
                    },
                ),
            ]
        ),
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
    schema = {'type': 'array', 'items': {'type': 'string'}, 'example': ['hi']}

    config = module._schema_to_sample_configuration(schema)

    assert config == ['hi']


def test_schema_to_sample_configuration_generates_config_sequence_of_maps_with_examples():
    flexmock(module.yaml.comments).should_receive('CommentedSeq').replace_with(list)
    flexmock(module).should_receive('add_comments_to_configuration_sequence')
    flexmock(module).should_receive('add_comments_to_configuration_object')
    schema = {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': OrderedDict(
                [('field1', {'example': 'Example 1'}), ('field2', {'example': 'Example 2'})]
            ),
        },
    }

    config = module._schema_to_sample_configuration(schema)

    assert config == [OrderedDict([('field1', 'Example 1'), ('field2', 'Example 2')])]


def test_schema_to_sample_configuration_with_unsupported_schema_raises():
    schema = {'gobbledygook': [{'type': 'not-your'}]}

    with pytest.raises(ValueError):
        module._schema_to_sample_configuration(schema)


def test_merge_source_configuration_into_destination_inserts_map_fields():
    destination_config = {'foo': 'dest1', 'bar': 'dest2'}
    source_config = {'foo': 'source1', 'baz': 'source2'}
    flexmock(module).should_receive('remove_commented_out_sentinel')
    flexmock(module).should_receive('yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {'foo': 'source1', 'bar': 'dest2', 'baz': 'source2'}


def test_merge_source_configuration_into_destination_inserts_nested_map_fields():
    destination_config = {'foo': {'first': 'dest1', 'second': 'dest2'}, 'bar': 'dest3'}
    source_config = {'foo': {'first': 'source1'}}
    flexmock(module).should_receive('remove_commented_out_sentinel')
    flexmock(module).should_receive('yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {'foo': {'first': 'source1', 'second': 'dest2'}, 'bar': 'dest3'}


def test_merge_source_configuration_into_destination_inserts_sequence_fields():
    destination_config = {'foo': ['dest1', 'dest2'], 'bar': ['dest3'], 'baz': ['dest4']}
    source_config = {'foo': ['source1'], 'bar': ['source2', 'source3']}
    flexmock(module).should_receive('remove_commented_out_sentinel')
    flexmock(module).should_receive('yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {
        'foo': ['source1'],
        'bar': ['source2', 'source3'],
        'baz': ['dest4'],
    }


def test_merge_source_configuration_into_destination_inserts_sequence_of_maps():
    destination_config = {'foo': [{'first': 'dest1', 'second': 'dest2'}], 'bar': 'dest3'}
    source_config = {'foo': [{'first': 'source1'}, {'other': 'source2'}]}
    flexmock(module).should_receive('remove_commented_out_sentinel')
    flexmock(module).should_receive('yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {
        'foo': [{'first': 'source1', 'second': 'dest2'}, {'other': 'source2'}],
        'bar': 'dest3',
    }


def test_merge_source_configuration_into_destination_without_source_does_nothing():
    original_destination_config = {'foo': 'dest1', 'bar': 'dest2'}
    destination_config = dict(original_destination_config)

    module.merge_source_configuration_into_destination(destination_config, None)

    assert destination_config == original_destination_config
