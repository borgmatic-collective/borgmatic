import os
import signal


def _handle_signal(signal_number, frame):  # pragma: no cover
    '''
    Send the signal to all processes in borgmatic's process group, which includes child processes.
    '''
    # Prevent infinite signal handler recursion. If the parent frame is this very same handler
    # function, we know we're recursing.
    if frame.f_back.f_code.co_name == _handle_signal.__name__:
        return

    os.killpg(os.getpgrp(), signal_number)


def configure_signals():  # pragma: no cover
    '''
    Configure borgmatic's signal handlers to pass relevant signals through to any child processes
    like Borg. Note that SIGINT gets passed through even without these changes.
    '''
    for signal_number in (signal.SIGHUP, signal.SIGTERM, signal.SIGUSR1, signal.SIGUSR2):
        signal.signal(signal_number, _handle_signal)
