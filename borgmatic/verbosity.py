import logging

import borgmatic.logger

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
        VERBOSITY_ERROR: logging.ERROR,
        VERBOSITY_ANSWER: logging.ANSWER,
        VERBOSITY_SOME: logging.INFO,
        VERBOSITY_LOTS: logging.DEBUG,
    }.get(verbosity, logging.WARNING)
