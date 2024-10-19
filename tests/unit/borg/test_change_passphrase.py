import logging

from flexmock import flexmock

import borgmatic.logger
from borgmatic.borg import change_passphrase as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    command, config=None, output_file=module.borgmatic.execute.DO_NOT_CAPTURE, borg_exit_codes=None
):
    borgmatic.logger.add_custom_log_levels()

    flexmock(module.environment).should_receive('make_environment').with_args(config or {}).once()
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        command,
        output_file=output_file,
        output_log_level=module.logging.ANSWER,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
        extra_environment=None,
    ).once()


def test_change_passphrase_calls_borg_with_required_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'key', 'change-passphrase', 'repo'))

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_change_passphrase_calls_borg_with_local_path():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1', 'key', 'change-passphrase', 'repo'))

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
        local_path='borg1',
    )


def test_change_passphrase_calls_borg_using_exit_codes():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    borg_exit_codes = flexmock()
    config = {'borg_exit_codes': borg_exit_codes}
    insert_execute_command_mock(
        ('borg', 'key', 'change-passphrase', 'repo'), config=config, borg_exit_codes=borg_exit_codes
    )

    module.change_passphrase(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_change_passphrase_calls_borg_with_remote_path_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(
        ('borg', 'key', 'change-passphrase', '--remote-path', 'borg1', 'repo')
    )

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
        remote_path='borg1',
    )


def test_change_passphrase_calls_borg_with_umask_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    config = {'umask': '0770'}
    insert_execute_command_mock(
        ('borg', 'key', 'change-passphrase', '--umask', '0770', 'repo'), config=config
    )

    module.change_passphrase(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_change_passphrase_calls_borg_with_log_json_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'key', 'change-passphrase', '--log-json', 'repo'))

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=True),
    )


def test_change_passphrase_calls_borg_with_lock_wait_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    config = {'lock_wait': '5'}
    insert_execute_command_mock(
        ('borg', 'key', 'change-passphrase', '--lock-wait', '5', 'repo'), config=config
    )

    module.change_passphrase(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_change_passphrase_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'key', 'change-passphrase', '--info', 'repo'))
    insert_logging_mock(logging.INFO)

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_change_passphrase_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(
        ('borg', 'key', 'change-passphrase', '--debug', '--show-rc', 'repo')
    )
    insert_logging_mock(logging.DEBUG)

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_change_passphrase_with_dry_run_skips_borg_call():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    module.change_passphrase(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=True, log_json=False),
    )


def test_change_passphrase_calls_borg_without_passphrase():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(
        ('borg', 'key', 'change-passphrase', 'repo'), config={'option': 'foo'}
    )

    module.change_passphrase(
        repository_path='repo',
        config={
            'encryption_passphrase': 'test',
            'encryption_passcommand': 'getpass',
            'option': 'foo',
        },
        local_borg_version='1.2.3',
        change_passphrase_arguments=flexmock(),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )
