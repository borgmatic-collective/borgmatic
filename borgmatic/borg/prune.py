import logging
import shlex

import borgmatic.config.paths
import borgmatic.logger
from borgmatic.borg import environment, feature, flags
from borgmatic.execute import execute_command

logger = logging.getLogger(__name__)


def make_prune_flags(config, prune_arguments, local_borg_version):
    '''
    Given a configuration dict mapping from option name to value, prune arguments as an
    argparse.Namespace instance, and the local Borg version, produce a corresponding sequence of
    command-line flags.

    For example, given a retention config of:

        {'keep_weekly': 4, 'keep_monthly': 6}

    This will be returned as an iterable of:

        (
            ('--keep-weekly', '4'),
            ('--keep-monthly', '6'),
        )
    '''
    flag_pairs = (
        ('--' + option_name.replace('_', '-'), str(value))
        for option_name, value in config.items()
        if option_name.startswith('keep_') and option_name != 'keep_exclude_tags'
    )
    prefix = config.get('prefix')

    return tuple(element for pair in flag_pairs for element in pair) + (
        (
            ('--match-archives', f'sh:{prefix}*')
            if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version)
            else ('--glob-archives', f'{prefix}*')
        )
        if prefix
        else (
            flags.make_match_archives_flags(
                config.get('match_archives'),
                config.get('archive_name_format'),
                local_borg_version,
            )
        )
    )


def prune_archives(
    dry_run,
    repository_path,
    config,
    local_borg_version,
    prune_arguments,
    global_arguments,
    local_path='borg',
    remote_path=None,
):
    '''
    Given dry-run flag, a local or remote repository path, and a configuration dict, prune Borg
    archives according to the retention policy specified in that configuration.
    '''
    borgmatic.logger.add_custom_log_levels()
    umask = config.get('umask', None)
    lock_wait = config.get('lock_wait', None)
    extra_borg_options = config.get('extra_borg_options', {}).get('prune', '')

    full_command = (
        (local_path, 'prune')
        + make_prune_flags(config, prune_arguments, local_borg_version)
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--umask', str(umask)) if umask else ())
        + (('--log-json',) if config.get('log_json') else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + (
            ('--stats',)
            if config.get('statistics')
            and not dry_run
            and not feature.available(feature.Feature.NO_PRUNE_STATS, local_borg_version)
            else ()
        )
        + (('--info',) if logger.getEffectiveLevel() == logging.INFO else ())
        + flags.make_flags_from_arguments(
            prune_arguments,
            excludes=('repository', 'match_archives', 'statistics', 'list_details'),
        )
        + (('--list',) if config.get('list_details') else ())
        + (('--debug', '--show-rc') if logger.isEnabledFor(logging.DEBUG) else ())
        + (('--dry-run',) if dry_run else ())
        + (tuple(shlex.split(extra_borg_options)) if extra_borg_options else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    if config.get('statistics') or config.get('list_details'):
        output_log_level = logging.ANSWER
    else:
        output_log_level = logging.INFO

    execute_command(
        full_command,
        output_log_level=output_log_level,
        environment=environment.make_environment(config),
        working_directory=borgmatic.config.paths.get_working_directory(config),
        borg_local_path=local_path,
        borg_exit_codes=config.get('borg_exit_codes'),
    )
