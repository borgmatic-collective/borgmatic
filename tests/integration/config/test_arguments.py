import pytest

from borgmatic.config import arguments as module


def test_convert_value_type_passes_through_non_string_value():
    assert module.convert_value_type([1, 2], 'array') == [1, 2]


def test_convert_value_type_passes_through_string_option_type():
    assert module.convert_value_type('foo', 'string') == 'foo'


def test_convert_value_type_parses_array_option_type():
    assert module.convert_value_type('[foo, bar]', 'array') == ['foo', 'bar']


def test_convert_value_type_with_array_option_type_and_no_array_raises():
    with pytest.raises(ValueError):
        module.convert_value_type('{foo, bar}', 'array')


def test_convert_value_type_parses_object_option_type():
    assert module.convert_value_type('{foo: bar}', 'object') == {'foo': 'bar'}


def test_convert_value_type_with_invalid_value_raises():
    with pytest.raises(ValueError):
        module.convert_value_type('{foo, bar', 'object')


def test_convert_value_type_with_unknown_option_type_raises():
    with pytest.raises(ValueError):
        module.convert_value_type('{foo, bar}', 'thingy')
