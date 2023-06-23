import logging
import sys

import borgmatic.commands.borgmatic


def main():
    warning_log = logging.makeLogRecord(
        dict(
            levelno=logging.WARNING,
            levelname='WARNING',
            msg='validate-borgmatic-config is deprecated and will be removed from a future release. Please use "borgmatic config validate" instead.',
        )
    )

    sys.argv = ['borgmatic', 'config', 'validate'] + sys.argv[1:]
    borgmatic.commands.borgmatic.main([warning_log])
