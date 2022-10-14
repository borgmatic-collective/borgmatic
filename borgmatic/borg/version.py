import logging

from borgmatic.borg import environment
from borgmatic.execute import execute_command_and_capture_output

logger = logging.getLogger(__name__)


def local_borg_version(storage_config, local_path='borg'):
    '''
    Given a storage configuration dict and a local Borg binary path, return a version string for it.

    Raise OSError or CalledProcessError if there is a problem running Borg.
    Raise ValueError if the version cannot be parsed.
    '''
    full_command = (
        (local_path, '--version')
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
    )
    output = execute_command_and_capture_output(
        full_command, extra_environment=environment.make_environment(storage_config),
    )

    try:
        return output.split(' ')[1].strip()
    except IndexError:
        raise ValueError('Could not parse Borg version string')
