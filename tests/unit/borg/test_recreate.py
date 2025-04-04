import logging
import shlex

from flexmock import flexmock

from borgmatic.borg import recreate as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, working_directory=None, borg_exit_codes=None):
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment')
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        full_command=command,
        output_log_level=module.logging.INFO,
        environment=None,
        working_directory=working_directory,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def test_recreate_archive_dry_run_skips_execution():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    recreate_arguments = flexmock(
        repository=flexmock(),
        list=None,
        target=None,
        comment=None,
        timestamp=None,
        match_archives=None,
    )

    result = module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=recreate_arguments,
        global_arguments=flexmock(log_json=False, dry_run=True),
        local_path='borg',
    )

    assert result is None


def test_recreate_calls_borg_with_required_flags():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        remote_path=None,
        patterns=None,
    )


def test_recreate_with_remote_path():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--remote-path', 'borg1', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        remote_path='borg1',
        patterns=None,
    )


def test_recreate_with_lock_wait():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--lock-wait', '5', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_log_info():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--info', '--repo', 'repo'))

    insert_logging_mock(logging.INFO)

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_log_debug():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--debug', '--show-rc', '--repo', 'repo'))
    insert_logging_mock(logging.DEBUG)

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_log_json():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--log-json', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=True),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_list_config_calls_borg_with_list_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    flexmock(module).should_receive('make_list_filter_flags').and_return('AME+-')
    insert_execute_command_mock(
        ('borg', 'recreate', '--list', '--filter', 'AME+-', '--repo', 'repo')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'list_details': True},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_patterns_from_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    mock_patterns_file = flexmock(name='patterns_file')
    flexmock(module).should_receive('write_patterns_file').and_return(mock_patterns_file)
    insert_execute_command_mock(
        ('borg', 'recreate', '--patterns-from', 'patterns_file', '--repo', 'repo')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=['pattern1', 'pattern2'],
    )


def test_recreate_with_exclude_flags():
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    flexmock(module).should_receive('make_exclude_flags').and_return(('--exclude', 'pattern'))
    insert_execute_command_mock(('borg', 'recreate', '--exclude', 'pattern', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'exclude_patterns': ['pattern']},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_target_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--target', 'new-archive', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target='new-archive',
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_comment_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(
        ('borg', 'recreate', '--comment', shlex.quote('This is a test comment'), '--repo', 'repo')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment='This is a test comment',
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_timestamp_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(
        ('borg', 'recreate', '--timestamp', '2023-10-01T12:00:00', '--repo', 'repo')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp='2023-10-01T12:00:00',
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_compression_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--compression', 'lz4', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'compression': 'lz4'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_chunker_params_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(
        ('borg', 'recreate', '--chunker-params', '19,23,21,4095', '--repo', 'repo')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'chunker_params': '19,23,21,4095'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_recompress_flag():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--recompress', 'always', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'recompress': 'always'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives=None,
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_match_archives_star():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_match_archives_regex():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='re:.*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_match_archives_shell():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(
        (
            '--repo',
            'repo',
        )
    )
    insert_execute_command_mock(('borg', 'recreate', '--repo', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='sh:*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_match_archives_and_feature_available_calls_borg_with_match_archives():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').with_args(
        'foo-*', None, '1.2.3'
    ).and_return(('--match-archives', 'foo-*'))
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    insert_execute_command_mock(('borg', 'recreate', '--repo', 'repo', '--match-archives', 'foo-*'))

    module.recreate_archive(
        repository='repo',
        archive=None,
        config={'match_archives': 'foo-*'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='foo-*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_archives_flag_and_feature_available_calls_borg_with_match_archives():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').with_args(
        'archive', None, '1.2.3'
    ).and_return(('--match-archives', 'archive'))
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('--repo', 'repo')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    insert_execute_command_mock(
        ('borg', 'recreate', '--repo', 'repo', '--match-archives', 'archive')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'match_archives': 'foo-*'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='foo-*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_match_archives_and_feature_not_available_calls_borg_without_match_archives():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').never()
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_archive_flags').never()
    insert_execute_command_mock(('borg', 'recreate', 'repo'))

    module.recreate_archive(
        repository='repo',
        archive=None,
        config={'match_archives': 'foo-*'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='foo-*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_archives_flags_and_feature_not_available_calls_borg_with_combined_repo_and_archive():
    flexmock(module.borgmatic.borg.create).should_receive('make_exclude_flags').and_return(())
    flexmock(module.borgmatic.borg.create).should_receive('write_patterns_file').and_return(None)
    flexmock(module.borgmatic.borg.create).should_receive('make_list_filter_flags').and_return('')
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').never()
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(('repo::archive',))
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').never()
    insert_execute_command_mock(('borg', 'recreate', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'match_archives': 'foo-*'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(
            list=None,
            target=None,
            comment=None,
            timestamp=None,
            match_archives='foo-*',
        ),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )
