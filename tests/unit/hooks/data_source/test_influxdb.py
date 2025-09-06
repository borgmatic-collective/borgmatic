import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import influxdb as module

def test_make_dump_path_creates_correct_path():
    assert module.make_dump_path('/tmp') == '/tmp/influxdb_databases'


def test_build_dump_command_creates_correct_command():
    # Example: influx backup --host https://myexample:8086 --skip-verify --token <REDACTED> \
    #  --org-id ccf6258c1e195e27 --bucket TestBucket .

    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'tls': True,
        'token': 'testtoken',
        'skip_verify': True,
        'http_debug': False,
        'organization_id': 'ccf6258c1e195e27',
        'bucket_name': "TestBucket"
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--skip-verify',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--org-id',
        'ccf6258c1e195e27',
        '--bucket',
        'TestBucket'
    )


def test_dump_data_sources_creates_named_pipe_and_executes_command():
    databases = [{'name': 'testdb', 'hostname': 'localhost'}]
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('/tmp/dumpfile')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').once()
    flexmock(module).should_receive('build_dump_command').and_return(('influx', 'backup'))
    flexmock(module).should_receive('execute_command').with_args(
        ('influx', 'backup'), run_to_completion=False
    ).once()

    processes = module.dump_data_sources(
        databases,
        config={},
        config_paths=[],
        borgmatic_runtime_directory='/tmp',
        patterns=[],
        dry_run=False,
    )

    assert len(processes) == 0  # No subprocess.Popen instances are returned.


def test_restore_data_source_dump_executes_restore_command():
    data_source = {'name': 'testdb', 'hostname': 'localhost'}
    connection_params = {'hostname': 'restorehost', 'token': 'restoretoken'}
    extract_process = flexmock(stdout=flexmock())
    flexmock(module).should_receive('build_restore_command').and_return(('influx', 'restore'))
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('influx', 'restore'),
        [extract_process],
        output_log_level=module.logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    module.restore_data_source_dump(
        hook_config={},
        config={},
        data_source=data_source,
        dry_run=False,
        extract_process=extract_process,
        connection_params=connection_params,
        borgmatic_runtime_directory='/tmp',
    )


def test_remove_data_source_dumps_removes_dumps():
    flexmock(module.dump).should_receive('remove_data_source_dumps').with_args(
        '/tmp/influxdb_databases', 'InfluxDB', False
    ).once()

    module.remove_data_source_dumps(
        databases=[],
        config={},
        borgmatic_runtime_directory='/tmp',
        dry_run=False,
    )
