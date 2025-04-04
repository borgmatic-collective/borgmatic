import logging
import os
import signal
import sys

logger = logging.getLogger(__name__)


EXIT_CODE_FROM_SIGNAL = 128


def handle_signal(signal_number, frame):
    '''
    Send the signal to all processes in borgmatic's process group, which includes child processes.
    '''
    # Prevent infinite signal handler recursion. If the parent frame is this very same handler
    # function, we know we're recursing.
    if frame.f_back.f_code.co_name == handle_signal.__name__:
        return

    os.killpg(os.getpgrp(), signal_number)

    if signal_number == signal.SIGTERM:
        logger.critical('Exiting due to TERM signal')
        sys.exit(EXIT_CODE_FROM_SIGNAL + signal.SIGTERM)
    elif signal_number == signal.SIGINT:
        # Borg doesn't always exit on a SIGINT, so give it a little encouragement.
        os.killpg(os.getpgrp(), signal.SIGTERM)

        raise KeyboardInterrupt()


def configure_signals():
    '''
    Configure borgmatic's signal handlers to pass relevant signals through to any child processes
    like Borg.
    '''
    for signal_number in (
        signal.SIGHUP,
        signal.SIGINT,
        signal.SIGTERM,
        signal.SIGUSR1,
        signal.SIGUSR2,
    ):
        signal.signal(signal_number, handle_signal)
