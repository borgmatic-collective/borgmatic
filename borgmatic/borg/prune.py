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


def prune_archives(verbosity, dry_run, repository, storage_config, retention_config,
                   local_path='borg', remote_path=None):
    '''
    Given verbosity/dry-run flags, a local or remote repository path, a storage config dict, and a
    retention config dict, prune Borg archives according the the retention policy specified in that
    configuration.
    '''
    remote_path_flags = ('--remote-path', remote_path) if remote_path else ()
    lock_wait = storage_config.get('lock_wait', None)
    lock_wait_flags = ('--lock-wait', str(lock_wait)) if lock_wait else ()
    verbosity_flags = {
        VERBOSITY_SOME: ('--info', '--stats',),
        VERBOSITY_LOTS: ('--debug', '--stats', '--list'),
    }.get(verbosity, ())
    dry_run_flags = ('--dry-run',) if dry_run else ()

    full_command = (
        local_path, 'prune',
        repository,
    ) + tuple(
        element
        for pair in _make_prune_flags(retention_config)
        for element in pair
    ) + remote_path_flags + lock_wait_flags + verbosity_flags + dry_run_flags

    logger.debug(' '.join(full_command))
    subprocess.check_call(full_command)
