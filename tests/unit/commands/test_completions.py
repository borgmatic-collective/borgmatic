from argparse import Action
from collections import namedtuple
from typing import Tuple

import pytest

from borgmatic.commands.completion import (
    has_choice_options,
    has_exact_options,
    has_file_options,
    has_unknown_required_param_options,
)

OptionType = namedtuple('OptionType', ['file', 'choice', 'unknown_required'])
TestCase = Tuple[Action, OptionType]

test_data: list[TestCase] = [
    (Action('--flag', 'flag'), OptionType(file=False, choice=False, unknown_required=False)),
    *(
        (
            Action('--flag', 'flag', metavar=metavar),
            OptionType(file=True, choice=False, unknown_required=False),
        )
        for metavar in ('FILENAME', 'PATH')
    ),
    (
        Action('--flag', dest='config_paths'),
        OptionType(file=True, choice=False, unknown_required=False),
    ),
    (
        Action('--flag', 'flag', metavar='OTHER'),
        OptionType(file=False, choice=False, unknown_required=False),
    ),
    (
        Action('--flag', 'flag', choices=['a', 'b']),
        OptionType(file=False, choice=True, unknown_required=False),
    ),
    (
        Action('--flag', 'flag', choices=['a', 'b'], type=str),
        OptionType(file=False, choice=True, unknown_required=True),
    ),
    (
        Action('--flag', 'flag', choices=None),
        OptionType(file=False, choice=False, unknown_required=False),
    ),
    (
        Action('--flag', 'flag', required=True),
        OptionType(file=False, choice=False, unknown_required=True),
    ),
    *(
        (
            Action('--flag', 'flag', nargs=nargs),
            OptionType(file=False, choice=False, unknown_required=True),
        )
        for nargs in ('+', '*')
    ),
    *(
        (
            Action('--flag', 'flag', metavar=metavar),
            OptionType(file=False, choice=False, unknown_required=True),
        )
        for metavar in ('PATTERN', 'KEYS', 'N')
    ),
    *(
        (
            Action('--flag', 'flag', type=type, default=None),
            OptionType(file=False, choice=False, unknown_required=True),
        )
        for type in (int, str)
    ),
    (
        Action('--flag', 'flag', type=int, default=1),
        OptionType(file=False, choice=False, unknown_required=False),
    ),
    (
        Action('--flag', 'flag', type=str, required=True, metavar='PATH'),
        OptionType(file=True, choice=False, unknown_required=True),
    ),
    (
        Action('--flag', 'flag', type=str, required=True, metavar='PATH', default='/dev/null'),
        OptionType(file=True, choice=False, unknown_required=True),
    ),
    (
        Action('--flag', 'flag', type=str, required=False, metavar='PATH', default='/dev/null'),
        OptionType(file=True, choice=False, unknown_required=False),
    ),
]


@pytest.mark.parametrize('action, option_type', test_data)
def test_has_file_options_detects_file_options(action: Action, option_type: OptionType):
    assert has_file_options(action) == option_type.file
    # if has_file_options(action) was true, has_exact_options(action) should also be true
    if option_type.file:
        assert has_exact_options(action)


@pytest.mark.parametrize('action, option_type', test_data)
def test_has_choice_options_detects_choice_options(action: Action, option_type: OptionType):
    assert has_choice_options(action) == option_type.choice
    # if has_choice_options(action) was true, has_exact_options(action) should also be true
    if option_type.choice:
        assert has_exact_options(action)


@pytest.mark.parametrize('action, option_type', test_data)
def test_has_unknown_required_param_options_detects_unknown_required_param_options(
    action: Action, option_type: OptionType
):
    assert has_unknown_required_param_options(action) == option_type.unknown_required
    # if has_unknown_required_param_options(action) was true, has_exact_options(action) should also be true
    if option_type.unknown_required:
        assert has_exact_options(action)


@pytest.mark.parametrize('action, option_type', test_data)
def test_has_exact_options_detects_exact_options(action: Action, option_type: OptionType):
    assert has_exact_options(action) == (
        option_type.file or option_type.choice or option_type.unknown_required
    )
