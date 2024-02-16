import pytest

from borgmatic.config import override as module


@pytest.mark.parametrize(
    'value,expected_result,option_type',
    (
        ('thing', 'thing', 'string'),
        ('33', 33, 'integer'),
        ('33', '33', 'string'),
        ('33b', '33b', 'integer'),
        ('33b', '33b', 'string'),
        ('true', True, 'boolean'),
        ('false', False, 'boolean'),
        ('true', 'true', 'string'),
        ('[foo]', ['foo'], 'array'),
        ('[foo]', '[foo]', 'string'),
        ('[foo, bar]', ['foo', 'bar'], 'array'),
        ('[foo, bar]', '[foo, bar]', 'string'),
    ),
)
def test_convert_value_type_coerces_values(value, expected_result, option_type):
    assert module.convert_value_type(value, option_type) == expected_result


def test_apply_overrides_updates_config():
    raw_overrides = [
        'section.key=value1',
        'other_section.thing=value2',
        'section.nested.key=value3',
        'location.no_longer_in_location=value4',
        'new.foo=bar',
        'new.mylist=[baz]',
        'new.nonlist=[quux]',
    ]
    config = {
        'section': {'key': 'value', 'other': 'other_value'},
        'other_section': {'thing': 'thing_value'},
        'no_longer_in_location': 'because_location_is_deprecated',
    }
    schema = {
        'properties': {
            'new': {'properties': {'mylist': {'type': 'array'}, 'nonlist': {'type': 'string'}}}
        }
    }

    module.apply_overrides(config, schema, raw_overrides)

    assert config == {
        'section': {'key': 'value1', 'other': 'other_value', 'nested': {'key': 'value3'}},
        'other_section': {'thing': 'value2'},
        'new': {'foo': 'bar', 'mylist': ['baz'], 'nonlist': '[quux]'},
        'location': {'no_longer_in_location': 'value4'},
        'no_longer_in_location': 'value4',
    }
