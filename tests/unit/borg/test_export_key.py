import logging

import pytest
from flexmock import flexmock

import borgmatic.logger
from borgmatic.borg import export_key as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, output_file=module.DO_NOT_CAPTURE):
    borgmatic.logger.add_custom_log_levels()

    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command,
        output_file=output_file,
        output_log_level=module.logging.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    ).once()


def test_export_key_calls_borg_with_required_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_calls_borg_with_remote_path_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--remote-path', 'borg1', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
        remote_path='borg1',
    )


def test_export_key_calls_borg_with_umask_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--umask', '0770', 'repo'))

    module.export_key(
        repository_path='repo',
        config={'umask': '0770'},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_calls_borg_with_log_json_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--log-json', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=True),
    )


def test_export_key_calls_borg_with_lock_wait_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--lock-wait', '5', 'repo'))

    module.export_key(
        repository_path='repo',
        config={'lock_wait': '5'},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--info', 'repo'))
    insert_logging_mock(logging.INFO)

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_with_log_debug_calls_borg_with_debug_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--debug', '--show-rc', 'repo'))
    insert_logging_mock(logging.DEBUG)

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_calls_borg_with_paper_flags():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--paper', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=True, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_calls_borg_with_paper_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--paper', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=True, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_calls_borg_with_qr_html_flag():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', '--qr-html', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=True, path=None),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_calls_borg_with_path_argument():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').and_return(False)
    insert_execute_command_mock(('borg', 'key', 'export', 'repo', 'dest'), output_file=None)

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path='dest'),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_with_already_existent_path_raises():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(FileExistsError):
        module.export_key(
            repository_path='repo',
            config={},
            local_borg_version='1.2.3',
            export_arguments=flexmock(paper=False, qr_html=False, path='dest'),
            global_arguments=flexmock(dry_run=False, log_json=False),
        )


def test_export_key_with_stdout_path_calls_borg_without_path_argument():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    insert_execute_command_mock(('borg', 'key', 'export', 'repo'))

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path='-'),
        global_arguments=flexmock(dry_run=False, log_json=False),
    )


def test_export_key_with_dry_run_skip_borg_call():
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.os.path).should_receive('exists').never()
    flexmock(module).should_receive('execute_command').never()

    module.export_key(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        export_arguments=flexmock(paper=False, qr_html=False, path=None),
        global_arguments=flexmock(dry_run=True, log_json=False),
    )
