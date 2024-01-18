import pytest
import ruamel.yaml
from flexmock import flexmock

from borgmatic.config import override as module


def test_set_values_with_empty_keys_bails():
    config = {}

    module.set_values(config, keys=(), value='value')

    assert config == {}


def test_set_values_with_one_key_sets_it_into_config():
    config = {}

    module.set_values(config, keys=('key',), value='value')

    assert config == {'key': 'value'}


def test_set_values_with_one_key_overwrites_existing_key():
    config = {'key': 'old_value', 'other': 'other_value'}

    module.set_values(config, keys=('key',), value='value')

    assert config == {'key': 'value', 'other': 'other_value'}


def test_set_values_with_multiple_keys_creates_hierarchy():
    config = {}

    module.set_values(config, ('option', 'suboption'), 'value')

    assert config == {'option': {'suboption': 'value'}}


def test_set_values_with_multiple_keys_updates_hierarchy():
    config = {'option': {'other': 'other_value'}}
    module.set_values(config, ('option', 'key'), 'value')

    assert config == {'option': {'key': 'value', 'other': 'other_value'}}


def test_set_values_with_key_when_list_index_expected_errors():
    config = {'option': ['foo', 'bar', 'baz']}

    with pytest.raises(ValueError):
        module.set_values(config, keys=('option', 'key'), value='value')


@pytest.mark.parametrize(
    'schema,option_keys,expected_type',
    (
        ({'properties': {'foo': {'type': 'array'}}}, ('foo',), 'array'),
        (
            {'properties': {'foo': {'properties': {'bar': {'type': 'array'}}}}},
            ('foo', 'bar'),
            'array',
        ),
        ({'properties': {'foo': {'type': 'array'}}}, ('other',), None),
        ({'properties': {'foo': {'description': 'stuff'}}}, ('foo',), None),
        ({}, ('foo',), None),
    ),
)
def test_type_for_option_grabs_type_if_found_in_schema(schema, option_keys, expected_type):
    assert module.type_for_option(schema, option_keys) == expected_type


@pytest.mark.parametrize(
    'key,expected_key',
    (
        (('foo', 'bar'), ('foo', 'bar')),
        (('location', 'foo'), ('foo',)),
        (('storage', 'foo'), ('foo',)),
        (('retention', 'foo'), ('foo',)),
        (('consistency', 'foo'), ('foo',)),
        (('output', 'foo'), ('foo',)),
        (('hooks', 'foo', 'bar'), ('foo', 'bar')),
        (('foo', 'hooks'), ('foo', 'hooks')),
    ),
)
def test_strip_section_names_passes_through_key_without_section_name(key, expected_key):
    assert module.strip_section_names(key) == expected_key


def test_parse_overrides_splits_keys_and_values():
    flexmock(module).should_receive('strip_section_names').replace_with(lambda value: value)
    flexmock(module).should_receive('type_for_option').and_return('string')
    flexmock(module).should_receive('convert_value_type').replace_with(
        lambda value, option_type: value
    )
    raw_overrides = ['option.my_option=value1', 'other_option=value2']
    expected_result = (
        (('option', 'my_option'), 'value1'),
        (('other_option'), 'value2'),
    )

    module.parse_overrides(raw_overrides, schema={}) == expected_result


def test_parse_overrides_allows_value_with_equal_sign():
    flexmock(module).should_receive('strip_section_names').replace_with(lambda value: value)
    flexmock(module).should_receive('type_for_option').and_return('string')
    flexmock(module).should_receive('convert_value_type').replace_with(
        lambda value, option_type: value
    )
    raw_overrides = ['option=this===value']
    expected_result = ((('option',), 'this===value'),)

    module.parse_overrides(raw_overrides, schema={}) == expected_result


def test_parse_overrides_raises_on_missing_equal_sign():
    flexmock(module).should_receive('strip_section_names').replace_with(lambda value: value)
    flexmock(module).should_receive('type_for_option').and_return('string')
    flexmock(module).should_receive('convert_value_type').replace_with(
        lambda value, option_type: value
    )
    raw_overrides = ['option']

    with pytest.raises(ValueError):
        module.parse_overrides(raw_overrides, schema={})


def test_parse_overrides_raises_on_invalid_override_value():
    flexmock(module).should_receive('strip_section_names').replace_with(lambda value: value)
    flexmock(module).should_receive('type_for_option').and_return('string')
    flexmock(module).should_receive('convert_value_type').and_raise(ruamel.yaml.parser.ParserError)
    raw_overrides = ['option=[in valid]']

    with pytest.raises(ValueError):
        module.parse_overrides(raw_overrides, schema={})


def test_parse_overrides_allows_value_with_single_key():
    flexmock(module).should_receive('strip_section_names').replace_with(lambda value: value)
    flexmock(module).should_receive('type_for_option').and_return('string')
    flexmock(module).should_receive('convert_value_type').replace_with(
        lambda value, option_type: value
    )
    raw_overrides = ['option=value']
    expected_result = ((('option',), 'value'),)

    module.parse_overrides(raw_overrides, schema={}) == expected_result


def test_parse_overrides_handles_empty_overrides():
    module.parse_overrides(raw_overrides=None, schema={}) == ()
