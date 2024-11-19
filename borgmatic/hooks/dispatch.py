import logging

from borgmatic.hooks import (
    apprise,
    cronhub,
    cronitor,
    healthchecks,
    loki,
    mariadb,
    mongodb,
    mysql,
    ntfy,
    pagerduty,
    postgresql,
    pushover,
    sqlite,
    uptimekuma,
    zabbix,
)

logger = logging.getLogger(__name__)

HOOK_NAME_TO_MODULE = {
    'apprise': apprise,
    'cronhub': cronhub,
    'cronitor': cronitor,
    'healthchecks': healthchecks,
    'loki': loki,
    'mariadb_databases': mariadb,
    'mongodb_databases': mongodb,
    'mysql_databases': mysql,
    'ntfy': ntfy,
    'pagerduty': pagerduty,
    'postgresql_databases': postgresql,
    'pushover': pushover,
    'sqlite_databases': sqlite,
    'uptime_kuma': uptimekuma,
    'zabbix': zabbix,
}


def call_hook(function_name, config, log_prefix, hook_name, *args, **kwargs):
    '''
    Given a configuration dict and a prefix to use in log entries, call the requested function of
    the Python module corresponding to the given hook name. Supply that call with the configuration
    for this hook (if any), the log prefix, and any given args and kwargs. Return any return value.

    Raise ValueError if the hook name is unknown.
    Raise AttributeError if the function name is not found in the module.
    Raise anything else that the called function raises.
    '''
    hook_config = config.get(hook_name, {})

    try:
        module = HOOK_NAME_TO_MODULE[hook_name]
    except KeyError:
        raise ValueError(f'Unknown hook name: {hook_name}')

    logger.debug(f'{log_prefix}: Calling {hook_name} hook function {function_name}')
    return getattr(module, function_name)(hook_config, config, log_prefix, *args, **kwargs)


def call_hooks(function_name, config, log_prefix, hook_names, *args, **kwargs):
    '''
    Given a configuration dict and a prefix to use in log entries, call the requested function of
    the Python module corresponding to each given hook name. Supply each call with the configuration
    for that hook, the log prefix, and any given args and kwargs. Collect any return values into a
    dict from hook name to return value.

    If the hook name is not present in the hooks configuration, then don't call the function for it
    and omit it from the return values.

    Raise ValueError if the hook name is unknown.
    Raise AttributeError if the function name is not found in the module.
    Raise anything else that a called function raises. An error stops calls to subsequent functions.
    '''
    return {
        hook_name: call_hook(function_name, config, log_prefix, hook_name, *args, **kwargs)
        for hook_name in hook_names
        if config.get(hook_name)
    }


def call_hooks_even_if_unconfigured(function_name, config, log_prefix, hook_names, *args, **kwargs):
    '''
    Given a configuration dict and a prefix to use in log entries, call the requested function of
    the Python module corresponding to each given hook name. Supply each call with the configuration
    for that hook, the log prefix, and any given args and kwargs. Collect any return values into a
    dict from hook name to return value.

    Raise AttributeError if the function name is not found in the module.
    Raise anything else that a called function raises. An error stops calls to subsequent functions.
    '''
    return {
        hook_name: call_hook(function_name, config, log_prefix, hook_name, *args, **kwargs)
        for hook_name in hook_names
    }
