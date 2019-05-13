import pytest

from borgmatic.logger import to_bool


@pytest.mark.parametrize('bool_val', (True, 'yes', 'on', '1', 'true', 'True', 1))
def test_logger_to_bool_is_true(bool_val):
    assert to_bool(bool_val)


@pytest.mark.parametrize('bool_val', (False, 'no', 'off', '0', 'false', 'False', 0))
def test_logger_to_bool_is_false(bool_val):
    assert not to_bool(bool_val)


def test_logger_to_bool_returns_none():
    assert to_bool(None) is None
