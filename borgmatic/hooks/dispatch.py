import enum
import importlib
import logging
import pkgutil

import borgmatic.hooks.command
import borgmatic.hooks.credential
import borgmatic.hooks.data_source
import borgmatic.hooks.monitoring

logger = logging.getLogger(__name__)


class Hook_type(enum.Enum):
    CREDENTIAL = 'credential'
    DATA_SOURCE = 'data_source'
    MONITORING = 'monitoring'


def get_submodule_names(parent_module):  # pragma: no cover
    '''
    Given a parent module, return the names of its direct submodules as a tuple of strings.
    '''
    return tuple(module_info.name for module_info in pkgutil.iter_modules(parent_module.__path__))


def call_hook(function_name, config, hook_name, *args, **kwargs):
    '''
    Given a configuration dict, call the requested function of the Python module corresponding to
    the given hook name. Supply that call with the configuration for this hook (if any) and any
    given args and kwargs. Return the return value of that call or None if the module in question is
    not a hook.

    Raise ValueError if the hook name is unknown.
    Raise AttributeError if the function name is not found in the module.
    Raise anything else that the called function raises.
    '''
    if hook_name in config or f'{hook_name}_databases' in config:
        hook_config = config.get(hook_name) or config.get(f'{hook_name}_databases') or {}
    else:
        hook_config = None

    module_name = hook_name.split('_databases')[0]

    # Probe for a data source or monitoring hook module corresponding to the hook name.
    for parent_module in (
        borgmatic.hooks.credential,
        borgmatic.hooks.data_source,
        borgmatic.hooks.monitoring,
    ):
        if module_name not in get_submodule_names(parent_module):
            continue

        module = importlib.import_module(f'{parent_module.__name__}.{module_name}')

        # If this module is explicitly flagged as not a hook, bail.
        if not getattr(module, 'IS_A_HOOK', True):
            return None

        break
    else:
        raise ValueError(f'Unknown hook name: {hook_name}')

    logger.debug(f'Calling {hook_name} hook function {function_name}')

    return getattr(module, function_name)(hook_config, config, *args, **kwargs)


def call_hooks(function_name, config, hook_type, *args, **kwargs):
    '''
    Given a configuration dict, call the requested function of the Python module corresponding to
    each hook of the given hook type ("credential", "data_source", or "monitoring"). Supply each
    call with the configuration for that hook, and any given args and kwargs.

    Collect any return values into a dict from module name to return value. Note that the module
    name is the name of the hook module itself, which might be different from the hook configuration
    option (e.g. "postgresql" for the former vs. "postgresql_databases" for the latter).

    If the hook name is not present in the hooks configuration, then don't call the function for it
    and omit it from the return values.

    Raise ValueError if the hook name is unknown.
    Raise AttributeError if the function name is not found in the module.
    Raise anything else that a called function raises. An error stops calls to subsequent functions.
    '''
    return {
        hook_name: call_hook(function_name, config, hook_name, *args, **kwargs)
        for hook_name in get_submodule_names(
            importlib.import_module(f'borgmatic.hooks.{hook_type.value}')
        )
        if hook_name in config or f'{hook_name}_databases' in config
    }


def call_hooks_even_if_unconfigured(function_name, config, hook_type, *args, **kwargs):
    '''
    Given a configuration dict, call the requested function of the Python module corresponding to
    each hook of the given hook type ("credential", "data_source", or "monitoring"). Supply each
    call with the configuration for that hook and any given args and kwargs. Collect any return
    values into a dict from hook name to return value.

    Raise AttributeError if the function name is not found in the module.
    Raise anything else that a called function raises. An error stops calls to subsequent functions.
    '''
    return {
        hook_name: call_hook(function_name, config, hook_name, *args, **kwargs)
        for hook_name in get_submodule_names(
            importlib.import_module(f'borgmatic.hooks.{hook_type.value}')
        )
    }
