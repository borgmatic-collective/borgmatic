import logging

from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def local_borg_version(local_path='borg'):
    '''
    Given a local Borg binary path, return a version string for it.

    Raise OSError or CalledProcessError if there is a problem running Borg.
    Raise ValueError if the version cannot be parsed.
    '''
    full_command = (
        (local_path, '--version')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
    )
    output = execute_command(full_command, output_log_level=None, borg_local_path=local_path)

    try:
        return output.split(' ')[1].strip()
    except IndexError:
        raise ValueError('Could not parse Borg version string')
