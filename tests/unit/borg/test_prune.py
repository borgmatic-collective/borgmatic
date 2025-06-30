import logging

from flexmock import flexmock

from borgmatic.borg import prune as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    prune_command, output_log_level, working_directory=None, borg_exit_codes=None
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        prune_command,
        output_log_level=output_log_level,
        environment=None,
        working_directory=working_directory,
        borg_local_path=prune_command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


BASE_PRUNE_FLAGS = ('--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly', '3')


def test_make_prune_flags_returns_flags_from_config():
    config = {
        'keep_daily': 1,
        'keep_weekly': 2,
        'keep_monthly': 3,
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    assert result == BASE_PRUNE_FLAGS


def test_make_prune_flags_with_keep_13weekly_and_keep_3monthly():
    config = {
        'keep_13weekly': 4,
        'keep_3monthly': 5,
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    expected = (
        '--keep-13weekly',
        '4',
        '--keep-3monthly',
        '5',
    )

    assert result == expected


def test_make_prune_flags_accepts_prefix_with_placeholders():
    config = {
        'keep_daily': 1,
        'prefix': 'Documents_{hostname}-{now}',  # noqa: FS003
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    expected = (
        '--keep-daily',
        '1',
        '--match-archives',
        'sh:Documents_{hostname}-{now}*',  # noqa: FS003
    )

    assert result == expected


def test_make_prune_flags_with_prefix_without_borg_features_uses_glob_archives():
    config = {
        'keep_daily': 1,
        'prefix': 'Documents_{hostname}-{now}',  # noqa: FS003
    }
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    expected = (
        '--keep-daily',
        '1',
        '--glob-archives',
        'Documents_{hostname}-{now}*',  # noqa: FS003
    )

    assert result == expected


def test_make_prune_flags_prefers_prefix_to_archive_name_format():
    config = {
        'archive_name_format': 'bar-{now}',  # noqa: FS003
        'keep_daily': 1,
        'prefix': 'bar-',
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').never()

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    expected = (
        '--keep-daily',
        '1',
        '--match-archives',
        'sh:bar-*',  # noqa: FS003
    )

    assert result == expected


def test_make_prune_flags_without_prefix_uses_archive_name_format_instead():
    config = {
        'archive_name_format': 'bar-{now}',  # noqa: FS003
        'keep_daily': 1,
        'prefix': None,
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '1.2.3'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*')).once()

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    expected = (
        '--keep-daily',
        '1',
        '--match-archives',
        'sh:bar-*',  # noqa: FS003
    )

    assert result == expected


def test_make_prune_flags_without_prefix_uses_match_archives_option():
    config = {
        'archive_name_format': 'bar-{now}',  # noqa: FS003
        'match_archives': 'foo*',
        'keep_daily': 1,
        'prefix': None,
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'foo*', 'bar-{now}', '1.2.3'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*')).once()

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    expected = (
        '--keep-daily',
        '1',
        '--match-archives',
        'sh:bar-*',  # noqa: FS003
    )

    assert result == expected


def test_make_prune_flags_ignores_keep_exclude_tags_in_config():
    config = {
        'keep_daily': 1,
        'keep_exclude_tags': True,
    }
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    result = module.make_prune_flags(
        config, flexmock(match_archives=None), local_borg_version='1.2.3'
    )

    assert result == ('--keep-daily', '1')


PRUNE_COMMAND = ('borg', 'prune', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly', '3')


def test_prune_archives_calls_borg_with_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('repo',), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_log_info_calls_borg_with_info_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--info', 'repo'), logging.INFO)
    insert_logging_mock(logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        repository_path='repo',
        config={},
        dry_run=False,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_log_debug_calls_borg_with_debug_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--debug', '--show-rc', 'repo'), logging.INFO)
    insert_logging_mock(logging.DEBUG)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        repository_path='repo',
        config={},
        dry_run=False,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_dry_run_calls_borg_with_dry_run_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--dry-run', 'repo'), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        repository_path='repo',
        config={},
        dry_run=True,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_local_path_calls_borg_via_local_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(('borg1',) + PRUNE_COMMAND[1:] + ('repo',), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg1',
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_exit_codes_calls_borg_using_them():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    borg_exit_codes = flexmock()
    insert_execute_command_mock(
        ('borg',) + PRUNE_COMMAND[1:] + ('repo',),
        logging.INFO,
        borg_exit_codes=borg_exit_codes,
    )

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_remote_path_calls_borg_with_remote_path_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--remote-path', 'borg1', 'repo'), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        remote_path='borg1',
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_stats_config_calls_borg_with_stats_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--stats', 'repo'), module.borgmatic.logger.ANSWER)

    prune_arguments = flexmock(statistics=None, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'statistics': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_list_config_calls_borg_with_list_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--list', 'repo'), module.borgmatic.logger.ANSWER)

    prune_arguments = flexmock(statistics=False, list_details=None)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'list_details': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_umask_calls_borg_with_umask_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    config = {'umask': '077'}
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--umask', '077', 'repo'), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_log_json_calls_borg_with_log_json_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--log-json', 'repo'), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'log_json': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_lock_wait_calls_borg_with_lock_wait_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    config = {'lock_wait': 5}
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(PRUNE_COMMAND + ('--lock-wait', '5', 'repo'), logging.INFO)

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_extra_borg_options_calls_borg_with_extra_options():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(
        PRUNE_COMMAND + ('--extra', '--options', 'value with space', 'repo'), logging.INFO
    )

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'extra_borg_options': {'prune': '--extra --options "value with space"'}},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_with_date_based_matching_calls_borg_with_date_based_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        (
            '--newer',
            '1d',
            '--newest',
            '1y',
            '--older',
            '1m',
            '--oldest',
            '1w',
            '--match-archives',
            None,
        )
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        (
            'borg',
            'prune',
            '--keep-daily',
            '1',
            '--keep-weekly',
            '2',
            '--keep-monthly',
            '3',
            '--newer',
            '1d',
            '--newest',
            '1y',
            '--older',
            '1m',
            '--oldest',
            '1w',
            '--match-archives',
            None,
            '--repo',
            'repo',
        ),
        output_log_level=logging.INFO,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )

    prune_arguments = flexmock(
        statistics=False, list_details=False, newer='1d', newest='1y', older='1m', oldest='1w'
    )
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '1.2.3'
    ).and_return(False)
    insert_execute_command_mock(
        PRUNE_COMMAND + ('repo',), logging.INFO, working_directory='/working/dir'
    )

    prune_arguments = flexmock(statistics=False, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )


def test_prune_archives_calls_borg_without_stats_when_feature_is_not_available():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_prune_flags').and_return(BASE_PRUNE_FLAGS)
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.NO_PRUNE_STATS, '2.0.0b10'
    ).and_return(True)
    insert_execute_command_mock(PRUNE_COMMAND + ('repo',), logging.ANSWER)

    prune_arguments = flexmock(statistics=True, list_details=False)
    module.prune_archives(
        dry_run=False,
        repository_path='repo',
        config={'statistics': True},
        local_borg_version='2.0.0b10',
        global_arguments=flexmock(),
        prune_arguments=prune_arguments,
    )
