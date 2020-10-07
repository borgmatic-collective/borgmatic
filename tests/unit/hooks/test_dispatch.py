import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks import dispatch as module


def hook_function(config, log_prefix, thing, value):
    '''
    This test function gets mocked out below.
    '''
    pass


def test_call_hook_invokes_module_function_with_arguments_and_returns_value():
    hooks = {'super_hook': flexmock(), 'other_hook': flexmock()}
    expected_return_value = flexmock()
    test_module = sys.modules[__name__]
    flexmock(module).HOOK_NAME_TO_MODULE = {'super_hook': test_module}
    flexmock(test_module).should_receive('hook_function').with_args(
        hooks['super_hook'], 'prefix', 55, value=66
    ).and_return(expected_return_value).once()

    return_value = module.call_hook('hook_function', hooks, 'prefix', 'super_hook', 55, value=66)

    assert return_value == expected_return_value


def test_call_hook_without_hook_config_skips_call():
    hooks = {'other_hook': flexmock()}
    test_module = sys.modules[__name__]
    flexmock(module).HOOK_NAME_TO_MODULE = {'super_hook': test_module}
    flexmock(test_module).should_receive('hook_function').never()

    module.call_hook('hook_function', hooks, 'prefix', 'super_hook', 55, value=66)


def test_call_hook_without_corresponding_module_raises():
    hooks = {'super_hook': flexmock(), 'other_hook': flexmock()}
    test_module = sys.modules[__name__]
    flexmock(module).HOOK_NAME_TO_MODULE = {'other_hook': test_module}
    flexmock(test_module).should_receive('hook_function').never()

    with pytest.raises(ValueError):
        module.call_hook('hook_function', hooks, 'prefix', 'super_hook', 55, value=66)


def test_call_hooks_calls_each_hook_and_collects_return_values():
    hooks = {'super_hook': flexmock(), 'other_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module).should_receive('call_hook').and_return(
        expected_return_values['super_hook']
    ).and_return(expected_return_values['other_hook'])

    return_values = module.call_hooks('do_stuff', hooks, 'prefix', ('super_hook', 'other_hook'), 55)

    assert return_values == expected_return_values


def test_call_hooks_calls_skips_return_values_for_missing_hooks():
    hooks = {'super_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock()}
    flexmock(module).should_receive('call_hook').and_return(expected_return_values['super_hook'])

    return_values = module.call_hooks('do_stuff', hooks, 'prefix', ('super_hook', 'other_hook'), 55)

    assert return_values == expected_return_values


def test_call_hooks_calls_skips_return_values_for_null_hooks():
    hooks = {'super_hook': flexmock(), 'other_hook': None}
    expected_return_values = {'super_hook': flexmock()}
    flexmock(module).should_receive('call_hook').and_return(expected_return_values['super_hook'])

    return_values = module.call_hooks('do_stuff', hooks, 'prefix', ('super_hook', 'other_hook'), 55)

    assert return_values == expected_return_values
