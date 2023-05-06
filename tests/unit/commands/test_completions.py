from argparse import Action

import pytest

from borgmatic.commands.completion import has_exact_options, has_file_options

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
