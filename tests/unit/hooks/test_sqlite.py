import logging

import pytest
from flexmock import flexmock

from borgmatic.hooks import sqlite as module


def test_dump_databases_logs_and_skips_if_dump_already_exists():
    databases = [{'path': '/path/to/database', 'name': 'database'}]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module).should_receive('dump.make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(logging).should_receive('info')
    flexmock(logging).should_receive('warning')

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run = False) == []

def test_dump_databases_dumps_each_database():
    databases = [
        {'path': '/path/to/database1', 'name': 'database1'},
        {'path': '/path/to/database2', 'name': 'database2'},
    ]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module).should_receive('dump.make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(logging).should_receive('info')
    flexmock(logging).should_receive('warning')
    flexmock(module).should_receive('dump.create_parent_directory_for_dump')
    flexmock(module).should_receive('execute_command').and_return('process')

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run = False) == ['process', 'process']

def test_dump_databases_does_not_dump_if_dry_run():
    databases = [{'path': '/path/to/database', 'name': 'database'}]

    flexmock(module).should_receive('make_dump_path').and_return('/path/to/dump')
    flexmock(module).should_receive('dump.make_database_dump_filename').and_return(
        '/path/to/dump/database'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(logging).should_receive('info')
    flexmock(logging).should_receive('warning')
    flexmock(module).should_receive('dump.create_parent_directory_for_dump')

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run = True) == []

def test_restore_database_dump_restores_database():
    database_config = [{'path': '/path/to/database', 'name': 'database'}]
    extract_process = flexmock(stdout = flexmock())

    flexmock(module).should_receive('execute_command_with_processes').and_return('process')

    module.restore_database_dump(database_config, 'test.yaml', {}, dry_run = False, extract_process = extract_process)

def test_restore_database_dump_does_not_restore_database_if_dry_run():
    database_config = [{'path': '/path/to/database', 'name': 'database'}]
    extract_process = flexmock(stdout = flexmock())

    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_database_dump(database_config, 'test.yaml', {}, dry_run = True, extract_process = extract_process)

def test_restore_database_dump_raises_error_if_database_config_is_invalid():
    database_config = []
    extract_process = flexmock(stdout = flexmock())

    with pytest.raises(ValueError):
        module.restore_database_dump(database_config, 'test.yaml', {}, dry_run = False, extract_process = extract_process)