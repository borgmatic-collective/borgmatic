import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import transfer as module

from ..test_verbosity import insert_logging_mock


def test_transfer_archives_calls_borg_with_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_dry_run_calls_borg_with_dry_run_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('dry-run', True).and_return(
        ('--dry-run',)
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--repo', 'repo', '--dry-run'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=True,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_log_info_calls_borg_with_info_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--info', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.INFO)
    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_log_debug_calls_borg_with_debug_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--debug', '--show-rc', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.DEBUG)

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_archive_calls_borg_with_match_archives_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'archive', 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'archive'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--match-archives', 'archive', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive='archive', progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_match_archives_calls_borg_with_match_archives_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'sh:foo*', 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:foo*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--match-archives', 'sh:foo*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}', 'match_archives': 'sh:foo*'},  # noqa: FS003
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives='sh:foo*', source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_archive_name_format_calls_borg_with_match_archives_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--match-archives', 'sh:bar-*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_local_path_calls_borg_via_local_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg2', 'transfer', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg2',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
        local_path='borg2',
    )


def test_transfer_archives_with_exit_codes_calls_borg_using_them():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    borg_exit_codes = flexmock()
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_remote_path_calls_borg_with_remote_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'remote-path', 'borg2'
    ).and_return(('--remote-path', 'borg2'))
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--remote-path', 'borg2', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
        remote_path='borg2',
    )


def test_transfer_archives_with_umask_calls_borg_with_umask_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else ()
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--umask', '077', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'umask': '077'},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_log_json_calls_borg_with_log_json_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('log-json', True).and_return(
        ('--log-json',)
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'log_json': True},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_lock_wait_calls_borg_with_lock_wait_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('lock-wait', 5).and_return(
        ('--lock-wait', '5')
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    config = {'lock_wait': 5}
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--lock-wait', '5', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config=config,
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_progress_calls_borg_with_progress_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('progress', True).and_return(
        ('--progress',)
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--progress', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=module.DO_NOT_CAPTURE,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'progress': True},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )


@pytest.mark.parametrize('argument_name', ('upgrader', 'sort_by', 'first', 'last'))
def test_transfer_archives_passes_through_arguments_to_borg(argument_name):
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flag_name = f"--{argument_name.replace('_', ' ')}"
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        (flag_name, 'value')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', flag_name, 'value', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None,
            progress=None,
            match_archives=None,
            source_repository=None,
            **{argument_name: 'value'},
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_source_repository_calls_borg_with_other_repo_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('other-repo', 'other').and_return(
        ('--other-repo', 'other')
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--repo', 'repo', '--other-repo', 'other'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository='other'
        ),
        global_arguments=flexmock(),
    )


def test_transfer_archives_with_date_based_matching_calls_borg_with_date_based_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        ('--newer', '1d', '--newest', '1y', '--older', '1m', '--oldest', '1w')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        (
            'borg',
            'transfer',
            '--newer',
            '1d',
            '--newest',
            '1y',
            '--older',
            '1m',
            '--oldest',
            '1w',
            '--repo',
            'repo',
        ),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        transfer_arguments=flexmock(
            archive=None,
            progress=None,
            source_repository='other',
            newer='1d',
            newest='1y',
            older='1m',
            oldest='1w',
        ),
    )


def test_transfer_archives_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'transfer', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        environment=None,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    module.transfer_archives(
        dry_run=False,
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='2.3.4',
        transfer_arguments=flexmock(
            archive=None, progress=None, match_archives=None, source_repository=None
        ),
        global_arguments=flexmock(),
    )
