from argparse import Action

import pytest

from borgmatic.commands.completion import (
    has_choice_options,
    has_exact_options,
    has_file_options,
    has_unknown_required_param_options,
)

file_options_test_data = [
    (Action('--flag', 'flag'), False),
    (Action('--flag', 'flag', metavar='FILENAME'), True),
    (Action('--flag', 'flag', metavar='PATH'), True),
    (Action('--flag', dest='config_paths'), True),
    (Action('--flag', 'flag', metavar='OTHER'), False),
]


@pytest.mark.parametrize('action, expected', file_options_test_data)
def test_has_file_options_detects_file_options(action: Action, expected: bool):
    assert has_file_options(action) == expected
    # if has_file_options(action) was true, has_exact_options(action) should also be true
    if expected:
        assert has_exact_options(action)


choices_test_data = [
    (Action('--flag', 'flag'), False),
    (Action('--flag', 'flag', choices=['a', 'b']), True),
    (Action('--flag', 'flag', choices=None), False),
]


@pytest.mark.parametrize('action, expected', choices_test_data)
def test_has_choice_options_detects_choice_options(action: Action, expected: bool):
    assert has_choice_options(action) == expected
    # if has_choice_options(action) was true, has_exact_options(action) should also be true
    if expected:
        assert has_exact_options(action)


unknown_required_param_test_data = [
    (Action('--flag', 'flag'), False),
    (Action('--flag', 'flag', required=True), True),
    *((Action('--flag', 'flag', nargs=nargs), True) for nargs in ('+', '*')),
    *((Action('--flag', 'flag', metavar=metavar), True) for metavar in ('PATTERN', 'KEYS', 'N')),
    *((Action('--flag', 'flag', type=type, default=None), True) for type in (int, str)),
    (Action('--flag', 'flag', type=int, default=1), False),
]


@pytest.mark.parametrize('action, expected', unknown_required_param_test_data)
def test_has_unknown_required_param_options_detects_unknown_required_param_options(
    action: Action, expected: bool
):
    assert has_unknown_required_param_options(action) == expected
    # if has_unknown_required_param_options(action) was true, has_exact_options(action) should also be true
    if expected:
        assert has_exact_options(action)
