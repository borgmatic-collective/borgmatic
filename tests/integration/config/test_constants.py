import pytest
from flexmock import flexmock

from borgmatic.config import constants as module


def test_apply_constants_with_empty_constants_passes_through_value():
    assert module.apply_constants(value='thing', constants={}) == 'thing'


@pytest.mark.parametrize(
    'value,expected_value',
    (
        (None, None),
        ('thing', 'thing'),
        ('{foo}', 'bar'),
        ('abc{foo}', 'abcbar'),
        ('{foo}xyz', 'barxyz'),
        ('{foo}{baz}', 'barquux'),
        ('{int}', '3'),
        ('{bool}', 'True'),
        ('{unknown}', '{unknown}'),
        (['thing', 'other'], ['thing', 'other']),
        (['thing', '{foo}'], ['thing', 'bar']),
        (['{foo}', '{baz}'], ['bar', 'quux']),
        ({'key': 'value'}, {'key': 'value'}),
        ({'key': '{foo}'}, {'key': 'bar'}),
        ({'key': '{inject}'}, {'key': 'echo hi; naughty-command'}),
        ({'before_backup': '{inject}'}, {'before_backup': "'echo hi; naughty-command'"}),
        ({'after_backup': '{inject}'}, {'after_backup': "'echo hi; naughty-command'"}),
        ({'on_error': '{inject}'}, {'on_error': "'echo hi; naughty-command'"}),
        ({'run': '{inject}'}, {'run': "'echo hi; naughty-command'"}),
        ({'something': '{inject}'}, {'something': 'echo hi; naughty-command'}),
        (
            {
                'before_backup': '{env_pass}',
                'postgresql_databases': [{'name': 'users', 'password': '{env_pass}'}],
            },
            {
                'before_backup': "'${PASS}'",
                'postgresql_databases': [{'name': 'users', 'password': '${PASS}'}],
            },
        ),
        (3, 3),
        (True, True),
        (False, False),
        (r'\{foo\}', '{foo}'),
        (r'\{unknown\}', '{unknown}'),
        ({'run': r'\{foo\}'}, {'run': r'\{foo\}'}),
        ({'run': r'\{unknown\}'}, {'run': r'\{unknown\}'}),
    ),
)
def test_apply_constants_makes_string_substitutions(value, expected_value):
    flexmock(module).should_receive('coerce_scalar').replace_with(lambda value: value)
    constants = {
        'foo': 'bar',
        'baz': 'quux',
        'int': 3,
        'bool': True,
        'inject': 'echo hi; naughty-command',
        'env_pass': '${PASS}',
    }

    assert module.apply_constants(value, constants) == expected_value
