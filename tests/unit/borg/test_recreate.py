import logging

from flexmock import flexmock

from borgmatic.borg import recreate as module

from ..test_verbosity import insert_logging_mock

# from borgmatic.borg.pattern import Pattern, Pattern_type, Pattern_style, Pattern_source
# from borgmatic.borg.create import make_exclude_flags, make_list_filter_flags


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
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(('repo::archive',))
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    recreate_arguments = flexmock(repository=flexmock(), list=None, path=None)

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
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        remote_path=None,
        patterns=None,
    )


def test_recreate_with_remote_path():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', '--remote-path', 'borg1', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        remote_path='borg1',
        patterns=None,
    )


def test_recreate_with_lock_wait():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', '--lock-wait', '5', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_log_info():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', '--info', 'repo::archive'))

    insert_logging_mock(logging.INFO)

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_log_debug():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', '--debug', '--show-rc', 'repo::archive'))
    insert_logging_mock(logging.DEBUG)

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_log_json():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', '--log-json', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=True),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_path_flag():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(('borg', 'recreate', '--path', '/some/path', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path='/some/path', list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_list_filter_flags():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('AME+-')
    insert_execute_command_mock(
        ('borg', 'recreate', '--list', '--filter', 'AME+-', 'repo::archive')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=True),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )


def test_recreate_with_patterns_from_flag():
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo::archive',)
    )
    mock_patterns_file = flexmock(name='patterns_file')
    flexmock(module).should_receive('write_patterns_file').and_return(mock_patterns_file)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    insert_execute_command_mock(
        ('borg', 'recreate', '--patterns-from', 'patterns_file', 'repo::archive')
    )

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=['pattern1', 'pattern2'],
    )


def test_recreate_with_exclude_flags():
    flexmock(module.borgmatic.borg.flags).should_receive(
        'make_repository_archive_flags'
    ).and_return(('repo::archive',))
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return(None)
    # Mock the make_exclude_flags to return a sample exclude flag
    flexmock(module).should_receive('make_exclude_flags').and_return(('--exclude', 'pattern'))

    insert_execute_command_mock(('borg', 'recreate', '--exclude', 'pattern', 'repo::archive'))

    module.recreate_archive(
        repository='repo',
        archive='archive',
        config={'exclude_patterns': ['pattern']},
        local_borg_version='1.2.3',
        recreate_arguments=flexmock(path=None, list=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg',
        patterns=None,
    )
