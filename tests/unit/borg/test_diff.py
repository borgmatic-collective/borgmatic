import logging

from flexmock import flexmock

from borgmatic.borg import diff as module
from ..test_verbosity import insert_logging_mock

LOGGING_ANSWER = flexmock()


def test_diff_calls_borg_with_archives():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_local_path_calls_borg_with_it():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg6',
            'diff',
            '--log-json',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg6',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg6',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_remote_path_calls_borg_with_it():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--remote-path',
            'borg7',
            '--log-json',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path='borg7',
        patterns=[],
    )


def test_diff_with_lock_wait_calls_borg_with_it():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--lock-wait',
            '5',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={'lock_wait': 5},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_log_level_info_calls_borg_with_info_flag():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.logger).should_receive('getEffectiveLevel').and_return(logging.INFO)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--info',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_log_level_debug_calls_borg_with_debug_flags():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.logger).should_receive('isEnabledFor').and_return(logging.DEBUG)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--debug',
            '--show-rc',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_only_patterns_calls_borg_with_configured_pattern_paths():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    flexmock(module).should_receive('write_patterns_file').and_return(
        flexmock(name='/tmp/test_patterns')
    ).once()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--patterns-from',
            '/tmp/test_patterns',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=True,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_exclude_config_calls_borg_with_exclude_flags():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(
        ('--exclude', 'stuff')
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--exclude',
            'stuff',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_numeric_ids_calls_borg_with_numeric_ids_flag():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--numeric-ids',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={'numeric_ids': True},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_numeric_ids_and_feature_not_available_calls_borg_with_numeric_owner_flag():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').with_args(
        module.borgmatic.borg.feature.Feature.NUMERIC_IDS, object
    ).and_return(False)
    flexmock(module.borgmatic.borg.feature).should_receive('available').with_args(
        module.borgmatic.borg.feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, object
    ).and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--numeric-owner',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={'numeric_ids': True},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_same_chunker_params_calls_borg_with_it():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--same-chunker-params',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=True,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_sort_keys_calls_borg_with_formatted_sort_by_flags():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--sort-by',
            'foo,bar,baz',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=['foo', 'bar', 'baz'],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_content_only_calls_borg_with_it():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--content-only',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=True,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_with_extra_borg_options_calls_borg_with_them():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            '--extra',
            '--option',
            '--repo',
            'repo',
            'archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={'extra_borg_options': {'diff': '--extra --option'}},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )


def test_diff_without_separate_repository_archive_feature_available_calls_borg_joined_repository_archive():
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.borgmatic.borg.flags).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.borg.pattern).should_receive('write_patterns_file').and_return(
        flexmock(name='test')
    )
    flexmock(module.borgmatic.borg.feature).should_receive('available').with_args(
        module.borgmatic.borg.feature.Feature.NUMERIC_IDS, object
    ).and_return(True)
    flexmock(module.borgmatic.borg.feature).should_receive('available').with_args(
        module.borgmatic.borg.feature.Feature.SEPARATE_REPOSITORY_ARCHIVE, object
    ).and_return(False)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').never()
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(('repo::archive',))
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=(
            'borg',
            'diff',
            '--log-json',
            'repo::archive',
            'archive2',
        ),
        output_log_level=LOGGING_ANSWER,
        environment=environment,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    insert_logging_mock(logging.WARNING)

    module.borgmatic.borg.diff.diff(
        repository='repo',
        archive='archive',
        second_archive='archive2',
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive='archive2',
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
        patterns=[],
    )
