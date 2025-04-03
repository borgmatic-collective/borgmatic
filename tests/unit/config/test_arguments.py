import pytest
from flexmock import flexmock

from borgmatic.config import arguments as module


def test_set_values_without_keys_bails():
    config = {'option': 'value'}
    module.set_values(config=config, keys=(), value=5)

    assert config == {'option': 'value'}


def test_set_values_with_keys_adds_them_to_config():
    config = {'option': 'value'}

    module.set_values(config=config, keys=('foo', 'bar', 'baz'), value=5)

    assert config == {'option': 'value', 'foo': {'bar': {'baz': 5}}}


def test_set_values_with_one_existing_key_adds_others_to_config():
    config = {'foo': {'other': 'value'}}

    module.set_values(config=config, keys=('foo', 'bar', 'baz'), value=5)

    assert config == {'foo': {'other': 'value', 'bar': {'baz': 5}}}


def test_set_values_with_two_existing_keys_adds_others_to_config():
    config = {'foo': {'bar': {'other': 'value'}}}

    module.set_values(config=config, keys=('foo', 'bar', 'baz'), value=5)

    assert config == {'foo': {'bar': {'other': 'value', 'baz': 5}}}


def test_set_values_with_list_index_key_adds_it_to_config():
    config = {'foo': {'bar': [{'option': 'value'}, {'other': 'thing'}]}}

    module.set_values(config=config, keys=('foo', 'bar[1]', 'baz'), value=5)

    assert config == {'foo': {'bar': [{'option': 'value'}, {'other': 'thing', 'baz': 5}]}}


def test_set_values_with_list_index_key_out_of_range_raises():
    config = {'foo': {'bar': [{'option': 'value'}]}}

    with pytest.raises(ValueError):
        module.set_values(config=config, keys=('foo', 'bar[1]', 'baz'), value=5)


def test_set_values_with_final_list_index_key_out_of_range_raises():
    config = {'foo': {'bar': [{'option': 'value'}]}}

    with pytest.raises(ValueError):
        module.set_values(config=config, keys=('foo', 'bar[1]'), value=5)


def test_set_values_with_list_index_key_missing_list_and_out_of_range_raises():
    config = {'other': 'value'}

    with pytest.raises(ValueError):
        module.set_values(config=config, keys=('foo', 'bar[1]', 'baz'), value=5)


def test_set_values_with_final_list_index_key_adds_it_to_config():
    config = {'foo': {'bar': [1, 2]}}

    module.set_values(config=config, keys=('foo', 'bar[1]'), value=5)

    assert config == {'foo': {'bar': [1, 5]}}


def test_type_for_option_with_option_finds_type():
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').replace_with(
        lambda sub_schema: sub_schema['properties']
    )

    assert (
        module.type_for_option(
            schema={'type': 'object', 'properties': {'foo': {'type': 'integer'}}},
            option_keys=('foo',),
        )
        == 'integer'
    )


def test_type_for_option_with_nested_option_finds_type():
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').replace_with(
        lambda sub_schema: sub_schema['properties']
    )

    assert (
        module.type_for_option(
            schema={
                'type': 'object',
                'properties': {
                    'foo': {'type': 'object', 'properties': {'bar': {'type': 'boolean'}}}
                },
            },
            option_keys=('foo', 'bar'),
        )
        == 'boolean'
    )


def test_type_for_option_with_missing_nested_option_finds_nothing():
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').replace_with(
        lambda sub_schema: sub_schema['properties']
    )

    assert (
        module.type_for_option(
            schema={
                'type': 'object',
                'properties': {
                    'foo': {'type': 'object', 'properties': {'other': {'type': 'integer'}}}
                },
            },
            option_keys=('foo', 'bar'),
        )
        is None
    )


def test_type_for_option_with_typeless_nested_option_finds_nothing():
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').replace_with(
        lambda sub_schema: sub_schema['properties']
    )

    assert (
        module.type_for_option(
            schema={
                'type': 'object',
                'properties': {'foo': {'type': 'object', 'properties': {'bar': {'example': 5}}}},
            },
            option_keys=('foo', 'bar'),
        )
        is None
    )


def test_type_for_option_with_list_index_option_finds_type():
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').replace_with(
        lambda sub_schema: sub_schema['properties']
    )

    assert (
        module.type_for_option(
            schema={
                'type': 'object',
                'properties': {'foo': {'type': 'array', 'items': {'type': 'integer'}}},
            },
            option_keys=('foo[0]',),
        )
        == 'integer'
    )


def test_type_for_option_with_nested_list_index_option_finds_type():
    flexmock(module.borgmatic.config.schema).should_receive('get_properties').replace_with(
        lambda sub_schema: sub_schema['properties']
    )

    assert (
        module.type_for_option(
            schema={
                'type': 'object',
                'properties': {
                    'foo': {
                        'type': 'array',
                        'items': {'type': 'object', 'properties': {'bar': {'type': 'integer'}}},
                    }
                },
            },
            option_keys=('foo[0]', 'bar'),
        )
        == 'integer'
    )


def test_prepare_arguments_for_config_converts_arguments_to_keys():
    assert module.prepare_arguments_for_config(
        global_arguments=flexmock(**{'my_option.sub_option': 'value1', 'other_option': 'value2'}),
        schema={
            'type': 'object',
            'properties': {
                'my_option': {'type': 'object', 'properties': {'sub_option': {'type': 'string'}}},
                'other_option': {'type': 'string'},
            },
        },
    ) == (
        (('my_option', 'sub_option'), 'value1'),
        (('other_option',), 'value2'),
    )


def test_prepare_arguments_for_config_skips_option_with_none_value():
    assert module.prepare_arguments_for_config(
        global_arguments=flexmock(**{'my_option.sub_option': None, 'other_option': 'value2'}),
        schema={
            'type': 'object',
            'properties': {
                'my_option': {'type': 'object', 'properties': {'sub_option': {'type': 'string'}}},
                'other_option': {'type': 'string'},
            },
        },
    ) == ((('other_option',), 'value2'),)


def test_prepare_arguments_for_config_skips_option_missing_from_schema():
    assert module.prepare_arguments_for_config(
        global_arguments=flexmock(**{'my_option.sub_option': 'value1', 'other_option': 'value2'}),
        schema={
            'type': 'object',
            'properties': {
                'my_option': {'type': 'object'},
                'other_option': {'type': 'string'},
            },
        },
    ) == ((('other_option',), 'value2'),)


def test_apply_arguments_to_config_does_not_raise():
    flexmock(module).should_receive('prepare_arguments_for_config').and_return(
        (
            (('foo', 'bar'), 'baz'),
            (('one', 'two'), 'three'),
        )
    )
    flexmock(module).should_receive('set_values')

    module.apply_arguments_to_config(config={}, schema={}, arguments={'global': flexmock()})
