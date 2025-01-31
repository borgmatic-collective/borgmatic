import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks import dispatch as module


def hook_function(hook_config, config, thing, value):
    '''
    This test function gets mocked out below.
    '''
    pass


def test_call_hook_invokes_module_function_with_arguments_and_returns_value():
    config = {'super_hook': flexmock(), 'other_hook': flexmock()}
    expected_return_value = flexmock()
    test_module = sys.modules[__name__]
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.credential
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.data_source
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'third_hook'])
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring.super_hook'
    ).and_return(test_module)
    flexmock(test_module).should_receive('hook_function').with_args(
        config['super_hook'], config, 55, value=66
    ).and_return(expected_return_value).once()

    return_value = module.call_hook('hook_function', config, 'super_hook', 55, value=66)

    assert return_value == expected_return_value


def test_call_hook_probes_config_with_databases_suffix():
    config = {'super_hook_databases': flexmock(), 'other_hook': flexmock()}
    expected_return_value = flexmock()
    test_module = sys.modules[__name__]
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.credential
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.data_source
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'third_hook'])
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring.super_hook'
    ).and_return(test_module)
    flexmock(test_module).should_receive('hook_function').with_args(
        config['super_hook_databases'], config, 55, value=66
    ).and_return(expected_return_value).once()

    return_value = module.call_hook('hook_function', config, 'super_hook', 55, value=66)

    assert return_value == expected_return_value


def test_call_hook_strips_databases_suffix_from_hook_name():
    config = {'super_hook_databases': flexmock(), 'other_hook_databases': flexmock()}
    expected_return_value = flexmock()
    test_module = sys.modules[__name__]
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.credential
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.data_source
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'third_hook'])
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring.super_hook'
    ).and_return(test_module)
    flexmock(test_module).should_receive('hook_function').with_args(
        config['super_hook_databases'], config, 55, value=66
    ).and_return(expected_return_value).once()

    return_value = module.call_hook('hook_function', config, 'super_hook_databases', 55, value=66)

    assert return_value == expected_return_value


def test_call_hook_without_hook_config_invokes_module_function_with_arguments_and_returns_value():
    config = {'other_hook': flexmock()}
    expected_return_value = flexmock()
    test_module = sys.modules[__name__]
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.credential
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.data_source
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'third_hook'])
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring.super_hook'
    ).and_return(test_module)
    flexmock(test_module).should_receive('hook_function').with_args(
        None, config, 55, value=66
    ).and_return(expected_return_value).once()

    return_value = module.call_hook('hook_function', config, 'super_hook', 55, value=66)

    assert return_value == expected_return_value


def test_call_hook_without_corresponding_module_raises():
    config = {'super_hook': flexmock(), 'other_hook': flexmock()}
    test_module = sys.modules[__name__]
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.credential
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.data_source
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['some_hook'])
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring.super_hook'
    ).and_return(test_module)
    flexmock(test_module).should_receive('hook_function').never()

    with pytest.raises(ValueError):
        module.call_hook('hook_function', config, 'super_hook', 55, value=66)


def test_call_hook_skips_non_hook_modules():
    config = {'not_a_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.credential
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.data_source
    ).and_return(['other_hook'])
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['not_a_hook', 'third_hook'])
    not_a_hook_module = flexmock(IS_A_HOOK=False)
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring.not_a_hook'
    ).and_return(not_a_hook_module)

    return_value = module.call_hook('hook_function', config, 'not_a_hook', 55, value=66)

    assert return_value is None


def test_call_hooks_calls_each_hook_and_collects_return_values():
    config = {'super_hook': flexmock(), 'other_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring'
    ).and_return(module.borgmatic.hooks.monitoring)
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'other_hook'])
    flexmock(module).should_receive('call_hook').and_return(
        expected_return_values['super_hook']
    ).and_return(expected_return_values['other_hook'])

    return_values = module.call_hooks('do_stuff', config, module.Hook_type.MONITORING, 55)

    assert return_values == expected_return_values


def test_call_hooks_calls_skips_return_values_for_unconfigured_hooks():
    config = {'super_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock()}
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring'
    ).and_return(module.borgmatic.hooks.monitoring)
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'other_hook'])
    flexmock(module).should_receive('call_hook').and_return(expected_return_values['super_hook'])

    return_values = module.call_hooks('do_stuff', config, module.Hook_type.MONITORING, 55)

    assert return_values == expected_return_values


def test_call_hooks_calls_treats_null_hook_as_optionless():
    config = {'super_hook': flexmock(), 'other_hook': None}
    expected_return_values = {'super_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring'
    ).and_return(module.borgmatic.hooks.monitoring)
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'other_hook'])
    flexmock(module).should_receive('call_hook').and_return(
        expected_return_values['super_hook']
    ).and_return(expected_return_values['other_hook'])

    return_values = module.call_hooks('do_stuff', config, module.Hook_type.MONITORING, 55)

    assert return_values == expected_return_values


def test_call_hooks_calls_looks_up_databases_suffix_in_config():
    config = {'super_hook_databases': flexmock(), 'other_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring'
    ).and_return(module.borgmatic.hooks.monitoring)
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'other_hook'])
    flexmock(module).should_receive('call_hook').and_return(
        expected_return_values['super_hook']
    ).and_return(expected_return_values['other_hook'])

    return_values = module.call_hooks('do_stuff', config, module.Hook_type.MONITORING, 55)

    assert return_values == expected_return_values


def test_call_hooks_even_if_unconfigured_calls_each_hook_and_collects_return_values():
    config = {'super_hook': flexmock(), 'other_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring'
    ).and_return(module.borgmatic.hooks.monitoring)
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'other_hook'])
    flexmock(module).should_receive('call_hook').and_return(
        expected_return_values['super_hook']
    ).and_return(expected_return_values['other_hook'])

    return_values = module.call_hooks_even_if_unconfigured(
        'do_stuff', config, module.Hook_type.MONITORING, 55
    )

    assert return_values == expected_return_values


def test_call_hooks_even_if_unconfigured_calls_each_hook_configured_or_not_and_collects_return_values():
    config = {'other_hook': flexmock()}
    expected_return_values = {'super_hook': flexmock(), 'other_hook': flexmock()}
    flexmock(module.importlib).should_receive('import_module').with_args(
        'borgmatic.hooks.monitoring'
    ).and_return(module.borgmatic.hooks.monitoring)
    flexmock(module).should_receive('get_submodule_names').with_args(
        module.borgmatic.hooks.monitoring
    ).and_return(['super_hook', 'other_hook'])
    flexmock(module).should_receive('call_hook').and_return(
        expected_return_values['super_hook']
    ).and_return(expected_return_values['other_hook'])

    return_values = module.call_hooks_even_if_unconfigured(
        'do_stuff', config, module.Hook_type.MONITORING, 55
    )

    assert return_values == expected_return_values
