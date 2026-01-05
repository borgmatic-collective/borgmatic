import pytest

from borgmatic.config import constants as module


@pytest.mark.parametrize(
    'value,expected_value',
    (
        ('3', 3),
        ('0', 0),
        ('-3', -3),
        ('1234', 1234),
        ('true', True),
        ('True', True),
        ('false', False),
        ('False', False),
        ('thing', 'thing'),
        ({}, {}),
        ({'foo': 'bar'}, {'foo': 'bar'}),
        ([], []),
        (['foo', 'bar'], ['foo', 'bar']),
    ),
)
def test_coerce_scalar_converts_value(value, expected_value):
    assert module.coerce_scalar(value) == expected_value
