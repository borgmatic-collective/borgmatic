import pytest
from flexmock import flexmock

from borgmatic import logger as module


@pytest.mark.parametrize('bool_val', (True, 'yes', 'on', '1', 'true', 'True', 1))
def test_to_bool_parses_true_values(bool_val):
    assert module.to_bool(bool_val)


@pytest.mark.parametrize('bool_val', (False, 'no', 'off', '0', 'false', 'False', 0))
def test_to_bool_parses_false_values(bool_val):
    assert not module.to_bool(bool_val)


def test_to_bool_passes_none_through():
    assert module.to_bool(None) is None


def test_should_do_markup_respects_no_color_value():
    assert module.should_do_markup(no_color=True) is False


def test_should_do_markup_respects_PY_COLORS_environment_variable():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=False) is True


def test_should_do_markup_prefers_no_color_value_to_PY_COLORS():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=True) is False


def test_should_do_markup_respects_stdout_tty_value():
    flexmock(module.os.environ).should_receive('get').and_return(None)

    assert module.should_do_markup(no_color=False) is False


def test_should_do_markup_prefers_PY_COLORS_to_stdout_tty_value():
    flexmock(module.os.environ).should_receive('get').and_return('True')
    flexmock(module).should_receive('to_bool').and_return(True)

    assert module.should_do_markup(no_color=False) is True
