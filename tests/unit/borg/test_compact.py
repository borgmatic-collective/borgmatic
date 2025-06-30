import logging

from flexmock import flexmock

from borgmatic.borg import compact as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    compact_command, output_log_level, working_directory=None, borg_exit_codes=None
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory
    )
    flexmock(module).should_receive('execute_command').with_args(
        compact_command,
        output_log_level=output_log_level,
        environment=None,
        working_directory=working_directory,
        borg_local_path=compact_command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


COMPACT_COMMAND = ('borg', 'compact')


def test_compact_segments_calls_borg_with_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('repo',), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_log_info_calls_borg_with_info_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--info', 'repo'), logging.INFO)
    insert_logging_mock(logging.INFO)

    module.compact_segments(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        dry_run=False,
    )


def test_compact_segments_with_log_debug_calls_borg_with_debug_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--debug', '--show-rc', 'repo'), logging.INFO)
    insert_logging_mock(logging.DEBUG)

    module.compact_segments(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        dry_run=False,
    )


def test_compact_segments_with_dry_run_skips_borg_call_when_feature_unavailable():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.DRY_RUN_COMPACT, '1.2.3'
    ).and_return(False)
    flexmock(module.environment).should_receive('make_environment').never()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').never()
    flexmock(module).should_receive('execute_command').never()
    flexmock(logging).should_receive('info').with_args('Skipping compact (dry run)').once()

    module.compact_segments(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        dry_run=True,
    )


def test_compact_segments_with_dry_run_executes_borg_call_when_feature_available():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.DRY_RUN_COMPACT, '1.4.1'
    ).and_return(True)
    flexmock(module.environment).should_receive('make_environment').once()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').once()
    flexmock(module).should_receive('execute_command').once()

    module.compact_segments(
        repository_path='repo',
        config={},
        local_borg_version='1.4.1',
        global_arguments=flexmock(),
        dry_run=True,
    )


def test_compact_segments_with_local_path_calls_borg_via_local_path():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1',) + COMPACT_COMMAND[1:] + ('repo',), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg1',
    )


def test_compact_segments_with_exit_codes_calls_borg_using_them():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    borg_exit_codes = flexmock()
    insert_execute_command_mock(
        COMPACT_COMMAND + ('repo',), logging.INFO, borg_exit_codes=borg_exit_codes
    )

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_remote_path_calls_borg_with_remote_path_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--remote-path', 'borg1', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        remote_path='borg1',
    )


def test_compact_segments_with_progress_calls_borg_with_progress_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--progress', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={'progress': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_cleanup_commits_calls_borg_with_cleanup_commits_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--cleanup-commits', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        cleanup_commits=True,
    )


def test_compact_segments_with_threshold_calls_borg_with_threshold_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--threshold', '20', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={'compact_threshold': 20},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_umask_calls_borg_with_umask_flags():
    config = {'umask': '077'}
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--umask', '077', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_log_json_calls_borg_with_log_json_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--log-json', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={'log_json': True},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_lock_wait_calls_borg_with_lock_wait_flags():
    config = {'lock_wait': 5}
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(COMPACT_COMMAND + ('--lock-wait', '5', 'repo'), logging.INFO)

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_with_extra_borg_options_calls_borg_with_extra_options():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(
        COMPACT_COMMAND + ('--extra', '--options', 'value with space', 'repo'), logging.INFO
    )

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={'extra_borg_options': {'compact': '--extra --options "value with space"'}},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )


def test_compact_segments_calls_borg_with_working_directory():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(
        COMPACT_COMMAND + ('repo',), logging.INFO, working_directory='/working/dir'
    )

    module.compact_segments(
        dry_run=False,
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
    )
