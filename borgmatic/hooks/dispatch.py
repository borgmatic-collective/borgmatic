import logging

from borgmatic.hooks import (
    cronhub,
    cronitor,
    healthchecks,
    mongodb,
    mysql,
    ntfy,
    pagerduty,
    postgresql,
)

logger = logging.getLogger(__name__)

HOOK_NAME_TO_MODULE = {
    'cronhub': cronhub,
    'cronitor': cronitor,
    'healthchecks': healthchecks,
    'mongodb_databases': mongodb,
    'mysql_databases': mysql,
    'ntfy': ntfy,
    'pagerduty': pagerduty,
    'postgresql_databases': postgresql,
}


def call_hook(function_name, hooks, log_prefix, hook_name, *args, **kwargs):
    '''
    Given the hooks configuration dict and a prefix to use in log entries, call the requested
    function of the Python module corresponding to the given hook name. Supply that call with the
    configuration for this hook (if any), the log prefix, and any given args and kwargs. Return any
    return value.

    Raise ValueError if the hook name is unknown.
    Raise AttributeError if the function name is not found in the module.
    Raise anything else that the called function raises.
    '''
    config = hooks.get(hook_name, {})

    try:
        module = HOOK_NAME_TO_MODULE[hook_name]
    except KeyError:
        raise ValueError('Unknown hook name: {}'.format(hook_name))

    logger.debug('{}: Calling {} hook function {}'.format(log_prefix, hook_name, function_name))
    return getattr(module, function_name)(config, log_prefix, *args, **kwargs)


def call_hooks(function_name, hooks, log_prefix, hook_names, *args, **kwargs):
    '''
    Given the hooks configuration dict and a prefix to use in log entries, call the requested
    function of the Python module corresponding to each given hook name. Supply each call with the
    configuration for that hook, the log prefix, and any given args and kwargs. Collect any return
    values into a dict from hook name to return value.

    If the hook name is not present in the hooks configuration, then don't call the function for it
    and omit it from the return values.

    Raise ValueError if the hook name is unknown.
    Raise AttributeError if the function name is not found in the module.
    Raise anything else that a called function raises. An error stops calls to subsequent functions.
    '''
    return {
        hook_name: call_hook(function_name, hooks, log_prefix, hook_name, *args, **kwargs)
        for hook_name in hook_names
        if hooks.get(hook_name)
    }


def call_hooks_even_if_unconfigured(function_name, hooks, log_prefix, hook_names, *args, **kwargs):
    '''
    Given the hooks configuration dict and a prefix to use in log entries, call the requested
    function of the Python module corresponding to each given hook name. Supply each call with the
    configuration for that hook, the log prefix, and any given args and kwargs. Collect any return
    values into a dict from hook name to return value.

    Raise AttributeError if the function name is not found in the module.
    Raise anything else that a called function raises. An error stops calls to subsequent functions.
    '''
    return {
        hook_name: call_hook(function_name, hooks, log_prefix, hook_name, *args, **kwargs)
        for hook_name in hook_names
    }
