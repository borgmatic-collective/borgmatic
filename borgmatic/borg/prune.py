import logging
import subprocess

from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


logger = logging.getLogger(__name__)


def _make_prune_flags(retention_config):
    '''
    Given a retention config dict mapping from option name to value, tranform it into an iterable of
    command-line name-value flag pairs.

    For example, given a retention config of:

        {'keep_weekly': 4, 'keep_monthly': 6}

    This will be returned as an iterable of:

        (
            ('--keep-weekly', '4'),
            ('--keep-monthly', '6'),
        )
    '''
    if not retention_config.get('prefix'):
        retention_config['prefix'] = '{hostname}-'

    return (
        ('--' + option_name.replace('_', '-'), str(retention_config[option_name]))
        for option_name, value in retention_config.items()
    )


def prune_archives(verbosity, repository, retention_config, remote_path=None):
    '''
    Given a verbosity flag, a local or remote repository path, a retention config dict, prune Borg
    archives according the the retention policy specified in that configuration.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--stats', '--list'),
    }.get(verbosity, ())

    full_command = (
        'borg', 'prune',
        repository,
    ) + tuple(
        element
        for pair in _make_prune_flags(retention_config)
        for element in pair
    ) + remote_path_flags + verbosity_flags

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
