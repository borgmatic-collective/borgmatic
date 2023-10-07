import subprocess
import sys


def test_borgmatic_command_with_invalid_flag_shows_error_but_not_traceback():
    output = subprocess.run(
        'borgmatic -v 2 --invalid'.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ).stdout.decode(sys.stdout.encoding)

    assert 'Unrecognized argument' in output
    assert 'Traceback' not in output
