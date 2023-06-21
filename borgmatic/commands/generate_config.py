import logging
import sys

import borgmatic.commands.borgmatic


def main():
    warning_log = logging.makeLogRecord(
        dict(
            levelno=logging.WARNING,
            levelname='WARNING',
            msg='generate-borgmatic-config is deprecated and will be removed from a future release. Please use "borgmatic config generate" instead.',
        )
    )

    sys.argv = ['borgmatic', 'config', 'generate'] + sys.argv[1:]
    borgmatic.commands.borgmatic.main([warning_log])
