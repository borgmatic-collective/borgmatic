import logging

from flexmock import flexmock

from borgmatic.borg import compact as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(compact_command, output_log_level):
    flexmock(module).should_receive('execute_command').with_args(
        compact_command, output_log_level=output_log_level, borg_local_path=compact_command[0]
    ).once()


COMPACT_COMMAND = ('borg', 'compact')


def test_compact_segments_calls_borg_with_parameters():
    insert_execute_command_mock(COMPACT_COMMAND + ('repo',), logging.WARNING)

    module.compact_segments(dry_run=False, repository='repo', storage_config={})


def test_compact_segments_with_log_info_calls_borg_with_info_parameter():
    insert_execute_command_mock(COMPACT_COMMAND + ('--info', 'repo'), logging.WARNING)
    insert_logging_mock(logging.INFO)

    module.compact_segments(repository='repo', storage_config={}, dry_run=False)


def test_compact_segments_with_log_debug_calls_borg_with_debug_parameter():
    insert_execute_command_mock(COMPACT_COMMAND + ('--debug', '--show-rc', 'repo'), logging.WARNING)
    insert_logging_mock(logging.DEBUG)

    module.compact_segments(repository='repo', storage_config={}, dry_run=False)


def test_compact_segments_with_dry_run_calls_borg_with_dry_run_parameter():
    insert_execute_command_mock(COMPACT_COMMAND + ('--dry-run', 'repo'), logging.WARNING)

    module.compact_segments(repository='repo', storage_config={}, dry_run=True)


def test_compact_segments_with_local_path_calls_borg_via_local_path():
    insert_execute_command_mock(('borg1',) + COMPACT_COMMAND[1:] + ('repo',), logging.WARNING)

    module.compact_segments(
        dry_run=False, repository='repo', storage_config={}, local_path='borg1',
    )


def test_compact_segments_with_remote_path_calls_borg_with_remote_path_parameters():
    insert_execute_command_mock(
        COMPACT_COMMAND + ('--remote-path', 'borg1', 'repo'), logging.WARNING
    )

    module.compact_segments(
        dry_run=False, repository='repo', storage_config={}, remote_path='borg1',
    )


def test_compact_segments_with_progress_calls_borg_with_progress_parameter():
    insert_execute_command_mock(COMPACT_COMMAND + ('--progress', 'repo'), logging.WARNING)

    module.compact_segments(
        dry_run=False, repository='repo', storage_config={}, progress=True,
    )


def test_compact_segments_with_cleanup_commits_calls_borg_with_cleanup_commits_parameter():
    insert_execute_command_mock(COMPACT_COMMAND + ('--cleanup-commits', 'repo'), logging.WARNING)

    module.compact_segments(
        dry_run=False, repository='repo', storage_config={}, cleanup_commits=True,
    )


def test_compact_segments_with_threshold_calls_borg_with_threshold_parameter():
    insert_execute_command_mock(COMPACT_COMMAND + ('--threshold', '20', 'repo'), logging.WARNING)

    module.compact_segments(
        dry_run=False, repository='repo', storage_config={}, threshold=20,
    )


def test_compact_segments_with_umask_calls_borg_with_umask_parameters():
    storage_config = {'umask': '077'}
    insert_execute_command_mock(COMPACT_COMMAND + ('--umask', '077', 'repo'), logging.WARNING)

    module.compact_segments(
        dry_run=False, repository='repo', storage_config=storage_config,
    )


def test_compact_segments_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    insert_execute_command_mock(COMPACT_COMMAND + ('--lock-wait', '5', 'repo'), logging.WARNING)

    module.compact_segments(
        dry_run=False, repository='repo', storage_config=storage_config,
    )


def test_compact_segments_with_extra_borg_options_calls_borg_with_extra_options():
    insert_execute_command_mock(COMPACT_COMMAND + ('--extra', '--options', 'repo'), logging.WARNING)

    module.compact_segments(
        dry_run=False,
        repository='repo',
        storage_config={'extra_borg_options': {'compact': '--extra --options'}},
    )
