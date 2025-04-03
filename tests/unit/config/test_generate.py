import pytest
from flexmock import flexmock

from borgmatic.config import generate as module


def test_schema_to_sample_configuration_generates_config_map_with_examples():
    schema = {
        'type': 'object',
        'properties': dict(
            [
                ('field1', {'type': 'string', 'example': 'Example 1'}),
                ('field2', {'type': 'string', 'example': 'Example 2'}),
                ('field3', {'type': 'string', 'example': 'Example 3'}),
            ]
        ),
    }
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').and_return(False)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'object', {'object'}
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'string', module.SCALAR_SCHEMA_TYPES, match=all
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').and_return(
        schema['properties']
    )
    flexmock(module.ruamel.yaml.comments).should_receive('CommentedMap').replace_with(dict)
    flexmock(module).should_receive('add_comments_to_configuration_object')

    config = module.schema_to_sample_configuration(schema)

    assert config == dict(
        [
            ('field1', 'Example 1'),
            ('field2', 'Example 2'),
            ('field3', 'Example 3'),
        ]
    )


def test_schema_to_sample_configuration_with_empty_object_generates_config_map_with_example():
    schema = {
        'type': 'object',
        'example': {
            'foo': 'Example 1',
            'baz': 'Example 2',
        },
    }
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').and_return(False)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'object', {'object'}
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'string', module.SCALAR_SCHEMA_TYPES, match=all
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').and_return({})
    flexmock(module.ruamel.yaml.comments).should_receive('CommentedMap').replace_with(dict)
    flexmock(module).should_receive('add_comments_to_configuration_object')

    config = module.schema_to_sample_configuration(schema)

    assert config == dict(
        [
            ('foo', 'Example 1'),
            ('baz', 'Example 2'),
        ]
    )


def test_schema_to_sample_configuration_generates_config_sequence_of_strings_with_example():
    flexmock(module.ruamel.yaml.comments).should_receive('CommentedSeq').replace_with(list)
    flexmock(module).should_receive('add_comments_to_configuration_sequence')
    schema = {'type': 'array', 'items': {'type': 'string'}, 'example': ['hi']}

    config = module.schema_to_sample_configuration(schema)

    assert config == ['hi']


def test_schema_to_sample_configuration_generates_config_sequence_of_maps_with_examples():
    schema = {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': dict(
                [
                    ('field1', {'type': 'string', 'example': 'Example 1'}),
                    ('field2', {'type': 'string', 'example': 'Example 2'}),
                ]
            ),
        },
    }
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').and_return(False)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'array', {'array'}
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'object', {'object'}
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'string', module.SCALAR_SCHEMA_TYPES, match=all
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').and_return(
        schema['items']['properties']
    )
    flexmock(module.ruamel.yaml.comments).should_receive('CommentedSeq').replace_with(list)
    flexmock(module).should_receive('add_comments_to_configuration_sequence')
    flexmock(module).should_receive('add_comments_to_configuration_object')

    config = module.schema_to_sample_configuration(schema)

    assert config == [dict([('field1', 'Example 1'), ('field2', 'Example 2')])]


def test_schema_to_sample_configuration_generates_config_sequence_of_maps_with_multiple_types():
    schema = {
        'type': 'array',
        'items': {
            'type': ['object', 'null'],
            'properties': dict(
                [
                    ('field1', {'type': 'string', 'example': 'Example 1'}),
                    ('field2', {'type': 'string', 'example': 'Example 2'}),
                ]
            ),
        },
    }
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').and_return(False)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'array', {'array'}
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        ['object', 'null'], {'object'}
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('compare_types').with_args(
        'string', module.SCALAR_SCHEMA_TYPES, match=all
    ).and_return(True)
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').and_return(
        schema['items']['properties']
    )
    flexmock(module.ruamel.yaml.comments).should_receive('CommentedSeq').replace_with(list)
    flexmock(module).should_receive('add_comments_to_configuration_sequence')
    flexmock(module).should_receive('add_comments_to_configuration_object')

    config = module.schema_to_sample_configuration(schema)

    assert config == [dict([('field1', 'Example 1'), ('field2', 'Example 2')])]


def test_schema_to_sample_configuration_with_unsupported_schema_raises():
    schema = {'gobbledygook': [{'type': 'not-your'}]}

    with pytest.raises(ValueError):
        module.schema_to_sample_configuration(schema)


def test_merge_source_configuration_into_destination_inserts_map_fields():
    destination_config = {'foo': 'dest1', 'bar': 'dest2'}
    source_config = {'foo': 'source1', 'baz': 'source2'}
    flexmock(module).should_receive('ruamel.yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {'foo': 'source1', 'bar': 'dest2', 'baz': 'source2'}


def test_merge_source_configuration_into_destination_inserts_nested_map_fields():
    destination_config = {'foo': {'first': 'dest1', 'second': 'dest2'}, 'bar': 'dest3'}
    source_config = {'foo': {'first': 'source1'}}
    flexmock(module).should_receive('ruamel.yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {'foo': {'first': 'source1', 'second': 'dest2'}, 'bar': 'dest3'}


def test_merge_source_configuration_into_destination_inserts_sequence_fields():
    destination_config = {'foo': ['dest1', 'dest2'], 'bar': ['dest3'], 'baz': ['dest4']}
    source_config = {'foo': ['source1'], 'bar': ['source2', 'source3']}
    flexmock(module).should_receive('ruamel.yaml.comments.CommentedSeq').replace_with(list)

    module.merge_source_configuration_into_destination(destination_config, source_config)

    assert destination_config == {
        'foo': ['source1'],
        'bar': ['source2', 'source3'],
        'baz': ['dest4'],
    }


def test_merge_source_configuration_into_destination_inserts_sequence_of_maps():
    destination_config = {'foo': [{'first': 'dest1', 'second': 'dest2'}], 'bar': 'dest3'}
    source_config = {'foo': [{'first': 'source1'}, {'other': 'source2'}]}
    flexmock(module).should_receive('ruamel.yaml.comments.CommentedSeq').replace_with(list)

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
