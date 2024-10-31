import argparse
import json
import logging

import borgmatic.config.paths
from borgmatic.borg import environment, feature, flags, repo_info
from borgmatic.execute import DO_NOT_CAPTURE, execute_command

logger = logging.getLogger(__name__)


def make_archive_filter_flags(local_borg_version, config, checks, check_arguments):
    '''
    Given the local Borg version, a configuration dict, a parsed sequence of checks, and check
    arguments as an argparse.Namespace instance, transform the checks into tuple of command-line
    flags for filtering archives in a check command.

    If "check_last" is set in the configuration and "archives" is in checks, then include a "--last"
    flag. And if "prefix" is set in configuration and "archives" is in checks, then include a
    "--match-archives" flag.
    '''
    check_last = config.get('check_last', None)
    prefix = config.get('prefix')

    if 'archives' in checks or 'data' in checks:
        return (('--last', str(check_last)) if check_last else ()) + (
            (
                ('--match-archives', f'sh:{prefix}*')
                if feature.available(feature.Feature.MATCH_ARCHIVES, local_borg_version)
                else ('--glob-archives', f'{prefix}*')
            )
            if prefix
            else (
                flags.make_match_archives_flags(
                    check_arguments.match_archives or config.get('match_archives'),
                    config.get('archive_name_format'),
                    local_borg_version,
                )
            )
        )

    if check_last:
        logger.warning(
            'Ignoring check_last option, as "archives" or "data" are not in consistency checks'
        )
    if prefix:
        logger.warning(
            'Ignoring consistency prefix option, as "archives" or "data" are not in consistency checks'
        )

    return ()


def make_check_name_flags(checks, archive_filter_flags):
    '''
    Given parsed checks set and a sequence of flags to filter archives, transform the checks into
    tuple of command-line check flags.

    For example, given parsed checks of:

        ('repository',)

    This will be returned as:

        ('--repository-only',)

    However, if both "repository" and "archives" are in checks, then omit them from the returned
    flags because Borg does both checks by default. If "data" is in checks, that implies "archives".
    '''
    if 'data' in checks:
        data_flags = ('--verify-data',)
        checks.update({'archives'})
    else:
        data_flags = ()

    common_flags = (archive_filter_flags if 'archives' in checks else ()) + data_flags

    if {'repository', 'archives'}.issubset(checks):
        return common_flags

    return (
        tuple(f'--{check}-only' for check in checks if check in ('repository', 'archives'))
        + common_flags
    )


def get_repository_id(
    repository_path, config, local_borg_version, global_arguments, local_path, remote_path
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, global
    arguments, and local/remote commands to run, return the corresponding Borg repository ID.

    Raise ValueError if the Borg repository ID cannot be determined.
    '''
    try:
        return json.loads(
            repo_info.display_repository_info(
                repository_path,
                config,
                local_borg_version,
                argparse.Namespace(json=True),
                global_arguments,
                local_path,
                remote_path,
            )
        )['repository']['id']
    except (json.JSONDecodeError, KeyError):
        raise ValueError(f'Cannot determine Borg repository ID for {repository_path}')


def check_archives(
    repository_path,
    config,
    local_borg_version,
    check_arguments,
    global_arguments,
    checks,
    archive_filter_flags,
    local_path='borg',
    remote_path=None,
):
    '''
    Given a local or remote repository path, a configuration dict, the local Borg version, check
    arguments as an argparse.Namespace instance, global arguments, a set of named Borg checks to run
    (some combination "repository", "archives", and/or "data"), archive filter flags, and
    local/remote commands to run, check the contained Borg archives for consistency.
    '''
    lock_wait = config.get('lock_wait')
    extra_borg_options = config.get('extra_borg_options', {}).get('check', '')

    verbosity_flags = ()
    if logger.isEnabledFor(logging.INFO):
        verbosity_flags = ('--info',)
    if logger.isEnabledFor(logging.DEBUG):
        verbosity_flags = ('--debug', '--show-rc')

    try:
        repository_check_config = next(
            check for check in config.get('checks', ()) if check.get('name') == 'repository'
        )
    except StopIteration:
        repository_check_config = {}

    if check_arguments.max_duration and 'archives' in checks:
        raise ValueError('The archives check cannot run when the --max-duration flag is used')
    if repository_check_config.get('max_duration') and 'archives' in checks:
        raise ValueError(
            'The archives check cannot run when the repository check has the max_duration option set'
        )

    max_duration = check_arguments.max_duration or repository_check_config.get('max_duration')

    borg_environment = environment.make_environment(config)
    borg_exit_codes = config.get('borg_exit_codes')

    full_command = (
        (local_path, 'check')
        + (('--repair',) if check_arguments.repair else ())
        + (('--max-duration', str(max_duration)) if max_duration else ())
        + make_check_name_flags(checks, archive_filter_flags)
        + (('--remote-path', remote_path) if remote_path else ())
        + (('--log-json',) if global_arguments.log_json else ())
        + (('--lock-wait', str(lock_wait)) if lock_wait else ())
        + verbosity_flags
        + (('--progress',) if check_arguments.progress else ())
        + (tuple(extra_borg_options.split(' ')) if extra_borg_options else ())
        + flags.make_repository_flags(repository_path, local_borg_version)
    )

    working_directory = borgmatic.config.paths.get_working_directory(config)

    # The Borg repair option triggers an interactive prompt, which won't work when output is
    # captured. And progress messes with the terminal directly.
    if check_arguments.repair or check_arguments.progress:
        execute_command(
            full_command,
            output_file=DO_NOT_CAPTURE,
            extra_environment=borg_environment,
            working_directory=working_directory,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
    else:
        execute_command(
            full_command,
            extra_environment=borg_environment,
            working_directory=working_directory,
            borg_local_path=local_path,
            borg_exit_codes=borg_exit_codes,
        )
