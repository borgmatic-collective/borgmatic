import pytest
from flexmock import flexmock

from borgmatic.hooks import sqlite as module


def test_dump_databases_logs_and_skips_if_dump_already_exists():
    databases = [{'path': '/path/to/database', 'name': 'database'}]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == []


def test_dump_databases_dumps_each_database():
    databases = [
        {'path': '/path/to/database1', 'name': 'database1'},
        {'path': '/path/to/database2', 'name': 'database2'},
    ]
    processes = [flexmock(), flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module).should_receive('execute_command').and_return(processes[0]).and_return(
        processes[1]
    )

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == processes


def test_dumping_database_with_non_existent_path_warns_and_dumps_database():
    databases = [
        {'path': '/path/to/database1', 'name': 'database1'},
    ]
    processes = [flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module).should_receive('execute_command').and_return(processes[0])

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == processes


def test_dumping_database_with_name_all_warns_and_dumps_all_databases():
    databases = [
        {'path': '/path/to/database1', 'name': 'all'},
    ]
    processes = [flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.logger).should_receive(
        'warning'
    ).twice()  # once for the name=all, once for the non-existent path
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module).should_receive('execute_command').and_return(processes[0])

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == processes


def test_dump_databases_does_not_dump_if_dry_run():
    databases = [{'path': '/path/to/database', 'name': 'database'}]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=True) == []


def test_restore_database_dump_restores_database():
    database_config = [{'path': '/path/to/database', 'name': 'database'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').once()

    flexmock(module.os).should_receive('remove').once()

    module.restore_database_dump(
        database_config,
        'test.yaml',
        {},
        dry_run=False,
        extract_process=extract_process,
        connection_params={'restore_path': None},
    )


def test_restore_database_dump_does_not_restore_database_if_dry_run():
    database_config = [{'path': '/path/to/database', 'name': 'database'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').never()
    flexmock(module.os).should_receive('remove').never()

    module.restore_database_dump(
        database_config,
        'test.yaml',
        {},
        dry_run=True,
        extract_process=extract_process,
        connection_params={'restore_path': None},
    )


def test_restore_database_dump_raises_error_if_database_config_is_invalid():
    database_config = []
    extract_process = flexmock(stdout=flexmock())

    with pytest.raises(ValueError):
        module.restore_database_dump(
            database_config,
            'test.yaml',
            {},
            dry_run=False,
            extract_process=extract_process,
            connection_params={'restore_path': None},
        )
