import logging

from borgmatic.execute import execute_command

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
    config = retention_config.copy()

    if 'prefix' not in config:
        config['prefix'] = '{hostname}-'
    elif not config['prefix']:
        config.pop('prefix')

    return (
        ('--' + option_name.replace('_', '-'), str(value)) for option_name, value in config.items()
    )


def prune_archives(
    dry_run,
    repository,
    storage_config,
    retention_config,
    local_path='borg',
    remote_path=None,
    stats=False,
    files=False,
):
    '''
    Given dry-run flag, a local or remote repository path, a storage config dict, and a
    retention config dict, prune Borg archives according to the retention policy specified in that
    configuration.
    '''
    umask = storage_config.get('umask', None)
    lock_wait = storage_config.get('lock_wait', None)
    extra_borg_options = storage_config.get('extra_borg_options', {}).get('prune', '')

    full_command = (
        (local_path, 'prune')
        + tuple(element for pair in _make_prune_flags(retention_config) for element in pair)
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--stats',) if stats and not dry_run else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--list',) if files else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + (repository,)
    )

    if (stats or files) and logger.getEffectiveLevel() == logging.WARNING:
        output_log_level = logging.WARNING
    else:
        output_log_level = logging.INFO

    execute_command(full_command, output_log_level=output_log_level, borg_local_path=local_path)
