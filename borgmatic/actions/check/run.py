import hashlib
import logging

import borgmatic.actions.check.frequency
import borgmatic.actions.check.spot
import borgmatic.actions.config.bootstrap
import borgmatic.actions.pattern
import borgmatic.borg.check
import borgmatic.borg.create
import borgmatic.borg.environment
import borgmatic.borg.extract
import borgmatic.borg.list
import borgmatic.borg.pattern
import borgmatic.borg.repo_list
import borgmatic.config.paths
import borgmatic.execute

DEFAULT_CHECKS = (
    {'name': 'repository', 'frequency': '1 month'},
    {'name': 'archives', 'frequency': '1 month'},
)


logger = logging.getLogger(__name__)


def parse_checks(config, only_checks=None):
    '''
    Given a configuration dict with a "checks" sequence of dicts and an optional list of override
    checks, return a tuple of named checks to run.

    For example, given a config of:

        {'checks': ({'name': 'repository'}, {'name': 'archives'})}

    This will be returned as:

        ('repository', 'archives')

    If no "checks" option is present in the config, return the DEFAULT_CHECKS. If a checks value
    has a name of "disabled", return an empty tuple, meaning that no checks should be run.
    '''
    checks = only_checks or tuple(
        check_config['name'] for check_config in (config.get('checks', None) or DEFAULT_CHECKS)
    )
    checks = tuple(check.lower() for check in checks)

    if 'disabled' in checks:
        logger.warning(
            'The "disabled" value for the "checks" option is deprecated and will be removed from a future release; use "skip_actions" instead',
        )

        if len(checks) > 1:
            logger.warning(
                'Multiple checks are configured, but one of them is "disabled"; not running any checks',
            )

        return ()

    return checks


def make_archives_check_id(archive_filter_flags):
    '''
    Given a sequence of flags to filter archives, return a unique hash corresponding to those
    particular flags. If there are no flags, return None.
    '''
    if not archive_filter_flags:
        return None

    return hashlib.sha256(' '.join(archive_filter_flags).encode()).hexdigest()


def run_check(
    config_filename,
    repository,
    config,
    local_borg_version,
    check_arguments,
    global_arguments,
    local_path,
    remote_path,
):
    '''
    Run the "check" action for the given repository.

    Raise ValueError if the Borg repository ID cannot be determined.
    '''
    logger.info('Running consistency checks')

    repository_id = (
        None
        if check_arguments.repair
        else borgmatic.borg.check.get_repository_id(
            repository['path'],
            config,
            local_borg_version,
            global_arguments,
            local_path=local_path,
            remote_path=remote_path,
        )
    )

    if repository_id:
        borgmatic.actions.check.frequency.upgrade_check_times(config, repository_id)

    configured_checks = parse_checks(config, check_arguments.only_checks)
    archive_filter_flags = borgmatic.borg.check.make_archive_filter_flags(
        local_borg_version,
        config,
        configured_checks,
        check_arguments,
    )
    archives_check_id = make_archives_check_id(archive_filter_flags)
    checks = borgmatic.actions.check.frequency.filter_checks_on_frequency(
        config if 'checks' in config else config | {'checks': DEFAULT_CHECKS},
        repository_id,
        configured_checks,
        check_arguments.force or check_arguments.repair,
        archives_check_id,
    )
    borg_specific_checks = set(checks).intersection({'repository', 'archives', 'data'})

    if borg_specific_checks:
        borgmatic.borg.check.check_archives(
            repository['path'],
            config,
            local_borg_version,
            check_arguments,
            global_arguments,
            borg_specific_checks,
            archive_filter_flags,
            local_path=local_path,
            remote_path=remote_path,
        )

        if repository_id:
            for check in borg_specific_checks:
                borgmatic.actions.check.frequency.write_check_time(
                    borgmatic.actions.check.frequency.make_check_time_path(
                        config, repository_id, check, archives_check_id
                    )
                )

    if 'extract' in checks:
        logger.info('Running extract check')
        borgmatic.borg.extract.extract_last_archive_dry_run(
            config,
            local_borg_version,
            global_arguments,
            repository['path'],
            config.get('lock_wait'),
            local_path,
            remote_path,
        )

        if repository_id:
            borgmatic.actions.check.frequency.write_check_time(
                borgmatic.actions.check.frequency.make_check_time_path(
                    config, repository_id, 'extract'
                )
            )

    if 'spot' in checks:
        logger.info('Running spot check')
        with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
            borgmatic.actions.check.spot.spot_check(
                repository,
                config,
                local_borg_version,
                global_arguments,
                local_path,
                remote_path,
                borgmatic_runtime_directory,
            )

        if repository_id:
            borgmatic.actions.check.frequency.write_check_time(
                borgmatic.actions.check.frequency.make_check_time_path(
                    config, repository_id, 'spot'
                )
            )
