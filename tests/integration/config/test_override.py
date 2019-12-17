import pytest

from borgmatic.config import override as module


@pytest.mark.parametrize(
    'value,expected_result',
    (
        ('thing', 'thing'),
        ('33', 33),
        ('33b', '33b'),
        ('true', True),
        ('false', False),
        ('[foo]', ['foo']),
        ('[foo, bar]', ['foo', 'bar']),
    ),
)
def test_convert_value_type_coerces_values(value, expected_result):
    assert module.convert_value_type(value) == expected_result


def test_apply_overrides_updates_config():
    raw_overrides = [
        'section.key=value1',
        'other_section.thing=value2',
        'section.nested.key=value3',
        'new.foo=bar',
    ]
    config = {
        'section': {'key': 'value', 'other': 'other_value'},
        'other_section': {'thing': 'thing_value'},
    }

    module.apply_overrides(config, raw_overrides)

    assert config == {
        'section': {'key': 'value1', 'other': 'other_value', 'nested': {'key': 'value3'}},
        'other_section': {'thing': 'value2'},
        'new': {'foo': 'bar'},
    }
