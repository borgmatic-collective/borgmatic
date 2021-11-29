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

    module.set_values(config, ('section', 'key'), 'value')

    assert config == {'section': {'key': 'value'}}


def test_set_values_with_multiple_keys_updates_hierarchy():
    config = {'section': {'other': 'other_value'}}
    module.set_values(config, ('section', 'key'), 'value')

    assert config == {'section': {'key': 'value', 'other': 'other_value'}}


def test_parse_overrides_splits_keys_and_values():
    flexmock(module).should_receive('convert_value_type').replace_with(lambda value: value)
    raw_overrides = ['section.my_option=value1', 'section.other_option=value2']
    expected_result = (
        (('section', 'my_option'), 'value1'),
        (('section', 'other_option'), 'value2'),
    )

    module.parse_overrides(raw_overrides) == expected_result


def test_parse_overrides_allows_value_with_equal_sign():
    flexmock(module).should_receive('convert_value_type').replace_with(lambda value: value)
    raw_overrides = ['section.option=this===value']
    expected_result = ((('section', 'option'), 'this===value'),)

    module.parse_overrides(raw_overrides) == expected_result


def test_parse_overrides_raises_on_missing_equal_sign():
    flexmock(module).should_receive('convert_value_type').replace_with(lambda value: value)
    raw_overrides = ['section.option']

    with pytest.raises(ValueError):
        module.parse_overrides(raw_overrides)


def test_parse_overrides_raises_on_invalid_override_value():
    flexmock(module).should_receive('convert_value_type').and_raise(ruamel.yaml.parser.ParserError)
    raw_overrides = ['section.option=[in valid]']

    with pytest.raises(ValueError):
        module.parse_overrides(raw_overrides)


def test_parse_overrides_allows_value_with_single_key():
    flexmock(module).should_receive('convert_value_type').replace_with(lambda value: value)
    raw_overrides = ['option=value']
    expected_result = ((('option',), 'value'),)

    module.parse_overrides(raw_overrides) == expected_result


def test_parse_overrides_handles_empty_overrides():
    module.parse_overrides(raw_overrides=None) == ()
