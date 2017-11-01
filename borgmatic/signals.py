import os
import signal


def _handle_signal(signal_number, frame):  # pragma: no cover
    '''
    Send the signal to all processes in borgmatic's process group, which includes child process.
    '''
    os.killpg(os.getpgrp(), signal_number)


def configure_signals():  # pragma: no cover
    '''
    Configure borgmatic's signal handlers to pass relevant signals through to any child processes
    like Borg.
    '''
    signal.signal(signal.SIGTERM, _handle_signal)
