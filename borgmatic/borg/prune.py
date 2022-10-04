import logging

from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def make_prune_flags(retention_config, local_borg_version):
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
    prefix = config.pop('prefix', '{hostname}-')

    if prefix:
        if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version):
            config['match_archives'] = f'sh:{prefix}*'
        else:
            config['glob_archives'] = f'{prefix}*'

    return (
        ('--' + option_name.replace('_', '-'), str(value)) for option_name, value in config.items()
    )


def prune_archives(
    dry_run,
    repository,
    storage_config,
    retention_config,
    local_borg_version,
    local_path='borg',
    remote_path=None,
    stats=False,
    list_archives=False,
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
        + tuple(
            element
            for pair in make_prune_flags(retention_config, local_borg_version)
            for element in pair
        )
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (('--stats',) if stats and not dry_run else ())
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + (('--list',) if list_archives else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + flags.make_repository_flags(repository, local_borg_version)
    )

    if (stats or list_archives) and logger.getEffectiveLevel() == logging.WARNING:
        output_log_level = logging.WARNING
    else:
        output_log_level = logging.INFO

    execute_command(
        full_command,
        output_log_level=output_log_level,
        borg_local_path=local_path,
        extra_environment=environment.make_environment(storage_config),
    )
