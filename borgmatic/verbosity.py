import logging

import borgmatic.logger

VERBOSITY_DISABLED = -2
VERBOSITY_ERROR = -1
VERBOSITY_ANSWER = 0
VERBOSITY_SOME = 1
VERBOSITY_LOTS = 2


def verbosity_to_log_level(verbosity):
    '''
    Given a borgmatic verbosity value, return the corresponding Python log level.
    '''
    borgmatic.logger.add_custom_log_levels()

    return {
        VERBOSITY_DISABLED: logging.DISABLED,
        VERBOSITY_ERROR: logging.ERROR,
        VERBOSITY_ANSWER: logging.ANSWER,
        VERBOSITY_SOME: logging.INFO,
        VERBOSITY_LOTS: logging.DEBUG,
    }.get(verbosity, logging.WARNING)


DEFAULT_VERBOSITIES = {
    'verbosity': 0,
    'syslog_verbosity': -2,
    'log_file_verbosity': 1,
    'monitoring_verbosity': 1,
}


def get_verbosity(configs, option_name):
    '''
    Given a dict from configuration filename to configuration dict, and the name of a configuration
    verbosity option, return the maximum verbosity value from that option across the given
    configuration files.
    '''
    try:
        return max(
            verbosity
            for config in configs.values()
            for verbosity in (config.get(option_name, DEFAULT_VERBOSITIES[option_name]),)
            if verbosity is not None
        )
    except ValueError:
        return DEFAULT_VERBOSITIES[option_name]
