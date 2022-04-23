import logging

from flexmock import flexmock

from borgmatic.borg import borg as module

from ..test_verbosity import insert_logging_mock


def test_run_arbitrary_borg_calls_borg_with_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg'
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['break-lock'],
    )


def test_run_arbitrary_borg_with_log_info_calls_borg_with_info_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo', '--info'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )
    insert_logging_mock(logging.INFO)

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['break-lock'],
    )


def test_run_arbitrary_borg_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo', '--debug', '--show-rc'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )
    insert_logging_mock(logging.DEBUG)

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['break-lock'],
    )


def test_run_arbitrary_borg_with_lock_wait_calls_borg_with_lock_wait_parameters():
    storage_config = {'lock_wait': 5}
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo', '--lock-wait', '5'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config=storage_config, options=['break-lock'],
    )


def test_run_arbitrary_borg_with_archive_calls_borg_with_archive_parameter():
    storage_config = {}
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo::archive'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config=storage_config, options=['break-lock'], archive='archive',
    )


def test_run_arbitrary_borg_with_local_path_calls_borg_via_local_path():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1', 'break-lock', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg1'
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['break-lock'], local_path='borg1',
    )


def test_run_arbitrary_borg_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo', '--remote-path', 'borg1'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['break-lock'], remote_path='borg1',
    )


def test_run_arbitrary_borg_passes_borg_specific_parameters_to_borg():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo', '--progress'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['list', '--progress'],
    )


def test_run_arbitrary_borg_omits_dash_dash_in_parameters_passed_to_borg():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'break-lock', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['--', 'break-lock'],
    )


def test_run_arbitrary_borg_without_borg_specific_parameters_does_not_raise():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg',), output_log_level=logging.WARNING, borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=[],
    )


def test_run_arbitrary_borg_passes_key_sub_command_to_borg_before_repository():
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'key', 'export', 'repo'), output_log_level=logging.WARNING, borg_local_path='borg',
    )

    module.run_arbitrary_borg(
        repository='repo', storage_config={}, options=['key', 'export'],
    )
