import logging

from flexmock import flexmock

from borgmatic.hooks import sqlite as module


def test_dump_data_sources_logs_and_skips_if_dump_already_exists():
    databases = [{'path': '/path/to/database', 'name': 'database'}]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == []


def test_dump_data_sources_dumps_each_database():
    databases = [
        {'path': '/path/to/database1', 'name': 'database1'},
        {'path': '/path/to/database2', 'name': 'database2'},
    ]
    processes = [flexmock(), flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module).should_receive('execute_command').and_return(processes[0]).and_return(
        processes[1]
    )

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == processes


def test_dump_data_sources_with_path_injection_attack_gets_escaped():
    databases = [
        {'path': '/path/to/database1; naughty-command', 'name': 'database1'},
    ]
    processes = [flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module).should_receive('execute_command').with_args(
        (
            'sqlite3',
            "'/path/to/database1; naughty-command'",
            '.dump',
            '>',
            '/path/to/dump/database',
        ),
        shell=True,
        run_to_completion=False,
    ).and_return(processes[0])

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == processes


def test_dump_data_sources_with_non_existent_path_warns_and_dumps_database():
    databases = [
        {'path': '/path/to/database1', 'name': 'database1'},
    ]
    processes = [flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module).should_receive('execute_command').and_return(processes[0])

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == processes


def test_dump_data_sources_with_name_all_warns_and_dumps_all_databases():
    databases = [
        {'path': '/path/to/database1', 'name': 'all'},
    ]
    processes = [flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.logger).should_receive(
        'warning'
    ).twice()  # once for the name=all, once for the non-existent path
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module).should_receive('execute_command').and_return(processes[0])

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == processes


def test_dump_data_sources_does_not_dump_if_dry_run():
    databases = [{'path': '/path/to/database', 'name': 'database'}]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=True) == []


def test_restore_data_source_dump_restores_database():
    hook_config = [{'path': '/path/to/database', 'name': 'database'}, {'name': 'other'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'sqlite3',
            '/path/to/database',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    flexmock(module.os).should_receive('remove').once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={'restore_path': None},
    )


def test_restore_data_source_dump_with_connection_params_uses_connection_params_for_restore():
    hook_config = [
        {'path': '/path/to/database', 'name': 'database', 'restore_path': 'config/path/to/database'}
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'sqlite3',
            'cli/path/to/database',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    flexmock(module.os).should_receive('remove').once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'database'},
        dry_run=False,
        extract_process=extract_process,
        connection_params={'restore_path': 'cli/path/to/database'},
    )


def test_restore_data_source_dump_without_connection_params_uses_restore_params_in_config_for_restore():
    hook_config = [
        {'path': '/path/to/database', 'name': 'database', 'restore_path': 'config/path/to/database'}
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'sqlite3',
            'config/path/to/database',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    flexmock(module.os).should_receive('remove').once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={'restore_path': None},
    )


def test_restore_data_source_dump_does_not_restore_database_if_dry_run():
    hook_config = [{'path': '/path/to/database', 'name': 'database'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').never()
    flexmock(module.os).should_receive('remove').never()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'database'},
        dry_run=True,
        extract_process=extract_process,
        connection_params={'restore_path': None},
    )
