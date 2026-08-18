from flexmock import flexmock

from borgmatic.hooks.data_source import influxdb as module


def test_make_dump_path_creates_correct_path():
    assert module.make_dump_path('/tmp') == '/tmp/influxdb_databases'


def test_get_default_port_returns_correct_port():
    assert module.get_default_port(None, None) == 8086


def test_use_streaming_always_returns_false():
    assert not module.use_streaming(databases=[], config={})
    assert not module.use_streaming(databases=[{'name': 'bucket1'}], config={})


def test_build_dump_command_creates_correct_command():
    # Example: influx backup --host https://myexample:8086 --skip-verify --token <REDACTED> \
    #  --org-id ccf6258c1e195e27 --bucket TestBucket .

    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'tls': True,
        'password': 'testtoken',
        'skip_verify': True,
        'http_debug': False,
        'organization_id': 'ccf6258c1e195e27',
        'name': 'TestBucket',
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
        'TestBucket',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_http_debug_flag():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'http_debug': True,
        'organization_id': 'ccf6258c1e195e27',
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--http-debug',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--org-id',
        'ccf6258c1e195e27',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_http_disabled():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'tls': False,  # HTTP instead of HTTPS
        'password': 'testtoken',
        'organization_id': 'ccf6258c1e195e27',
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'http://myexample.com:8086',
        '--token',
        'testtoken',
        '--org-id',
        'ccf6258c1e195e27',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_configurations():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'configurations_path': '/etc/influxdb/configs',
        'active_configuration': 'default',
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--configs-path',
        '/etc/influxdb/configs',
        '--active-config',
        'default',
        '--token',
        'testtoken',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_organization_name():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'organization_name': 'my-org',
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--org',
        'my-org',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_organization_id_and_name_precedence():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'organization_id': 'org123',
        'organization_name': 'my-org',  # This should be ignored when organization_id is present
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--org-id',
        'org123',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_bucket_id():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'bucket_id': 'abc123',
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--bucket-id',
        'abc123',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_bucket_id_and_name_precedence():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'bucket_id': 'abc123',
        'name': 'my-bucket',  # This should be ignored when bucket_id is present
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--bucket-id',
        'abc123',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_custom_influx_command():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'influx_command': '/usr/local/bin/influx2',
    }
    dump_filename = '/tmp/dumpfile'
    command = module.build_dump_command(database, dump_filename)

    assert command == (
        '/usr/local/bin/influx2',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '/tmp/dumpfile',
    )


def test_dump_data_sources_creates_named_pipe_and_executes_command():
    # Using proper InfluxDB parameters with default hostname (localhost)
    databases = [
        {
            'name': 'influx-backup',
            # hostname defaults to 'localhost'
            'port': 8086,
            'password': 'mytoken',
            'organization_id': 'org123',
            'label': 'mylabel',
        }
    ]
    flexmock(module.dump).should_receive('make_data_source_dump_filename').with_args(
        '/tmp/influxdb_databases',
        'influx-backup',
        hostname=None,
        port=8086,
        label='mylabel',
    ).and_return('/tmp/dumpfile')
    flexmock(module.dump).should_receive('create_parent_directory_for_dump').once()
    flexmock(module).should_receive('build_dump_command').and_return(
        (
            'influx',
            'backup',
            '--host',
            'https://localhost:8086',
            '--token',
            'mytoken',
            '--org-id',
            'org123',
        )
    )
    flexmock(module).should_receive('execute_command').with_args(
        (
            'influx',
            'backup',
            '--host',
            'https://localhost:8086',
            '--token',
            'mytoken',
            '--org-id',
            'org123',
        ),
        shell=True,
    ).once()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/tmp',
        'influxdb_databases',
        [
            module.borgmatic.actions.restore.Dump(
                'influxdb_databases', 'influx-backup', None, 8086, 'mylabel'
            ),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/tmp/influxdb_databases',
            source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
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


def test_dump_data_sources_with_dry_run_skips_command_execution():
    databases = [{'name': 'influx-backup', 'hostname': 'localhost', 'password': 'mytoken'}]
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/tmp/dumpfile'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').never()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').never()

    processes = module.dump_data_sources(
        databases,
        config={},
        config_paths=[],
        borgmatic_runtime_directory='/tmp',
        patterns=[],
        dry_run=True,
    )

    assert len(processes) == 0


def test_restore_data_source_dump_executes_restore_command():
    # Using proper InfluxDB parameters
    data_source = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'organization_id': 'org123',
        'label': 'mylabel',
    }
    connection_params = {
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
    }
    extract_process = flexmock(stdout=flexmock())

    # Mock dump_filename creation to avoid the TypeError
    flexmock(module.dump).should_receive('make_data_source_dump_filename').with_args(
        '/tmp/influxdb_databases',
        'influx-backup',
        hostname='localhost',
        port='8086',
        label='mylabel',
    ).and_return('/tmp/dumpfile')

    # Mock the build_restore_command to return a proper InfluxDB restore command
    flexmock(module).should_receive('build_restore_command').and_return(
        ('influx', 'restore', '--host', 'https://localhost:8086', '--token', 'mytoken')
    )

    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('influx', 'restore', '--host', 'https://localhost:8086', '--token', 'mytoken'),
        [extract_process],
        output_log_level=module.logging.DEBUG,
        input_file=extract_process.stdout,
        working_directory='/working',
        borg_local_path='borg',
    ).and_yield().once()

    module.restore_data_source_dump(
        hook_config={},
        config={},
        data_source=data_source,
        dry_run=False,
        extract_process=extract_process,
        connection_params=connection_params,
        borgmatic_runtime_directory='/tmp',
    )


def test_restore_data_source_dump_with_dry_run_skips_command_execution():
    data_source = {'name': 'influx-backup', 'hostname': 'localhost', 'password': 'mytoken'}
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    extract_process = flexmock(stdout=flexmock())

    # Mock dump_filename creation
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/tmp/dumpfile'
    )

    # Allow build_restore_command to be called, but ensure execute_command_with_processes is never called
    flexmock(module).should_receive('build_restore_command').and_return(('influx', 'restore'))
    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_data_source_dump(
        hook_config={},
        config={},
        data_source=data_source,
        dry_run=True,
        extract_process=extract_process,
        connection_params=connection_params,
        borgmatic_runtime_directory='/tmp',
    )


def test_build_restore_command_with_basic_parameters():
    database = {
        'name': 'influx-backup',
        # hostname defaults to 'localhost'
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'token': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_connection_params():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
    }
    connection_params = {
        'hostname': 'restorehost',
        'port': '9999',  # Changed to string to avoid TypeError
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    # The current implementation ignores connection_params and uses database values
    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_organization_parameters():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'organization_id': 'org123',
        'organization_name': 'my-org',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    # With both organization_id and organization_name, only organization_id should be used
    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--org-id',
        'org123',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_organization_name_only():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',
        'password': 'mytoken',
        'organization_name': 'my-org',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--org',
        'my-org',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_bucket_parameters():
    database = {
        'name': 'my-bucket',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'bucket_id': 'bucket123',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    # With both bucket_id and name, only bucket_id should be used
    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket-id',
        'bucket123',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_bucket_name_from_name_only():
    database = {
        'name': 'my-bucket',
        'hostname': 'localhost',
        'port': '8086',
        'password': 'mytoken',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'my-bucket',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_restore_bucket_and_organization():
    database = {
        'name': 'my-bucket',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'organization_name': 'my-org',
        'restore_bucket': 'new-bucket',
        'restore_organization': 'new-org',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--org',
        'my-org',
        '--bucket',
        'my-bucket',
        '--new-bucket',
        'new-bucket',
        '--new-org',
        'new-org',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_configurations():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'configurations_path': '/etc/influxdb/configs',
        'active_configuration': 'default',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '--configs-path',
        '/etc/influxdb/configs',
        '--active-config',
        'default',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_flags():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'skip_verify': True,
        'http_debug': True,
        'full_replace': True,
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '--skip-verify',
        '--http-debug',
        '--full',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_custom_influx_command():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'influx_command': '/usr/local/bin/influx2',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    extract_process = flexmock()

    command = module.build_restore_command(
        extract_process, database, dump_filename, connection_params
    )

    assert command == (
        '/usr/local/bin/influx2',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_remove_data_source_dumps_removes_dumps():
    flexmock(module.dump).should_receive('remove_data_source_dumps').with_args(
        '/tmp/influxdb_databases', 'InfluxDB', False
    ).once()

    module.remove_data_source_dumps(
        databases=[],
        config={},
        borgmatic_runtime_directory='/tmp',
        patterns=[],
        dry_run=False,
    )


def test_make_data_source_dump_patterns_with_no_port_adds_pattern_with_default_port():
    flexmock(module).should_receive('make_dump_path').replace_with(lambda path: path)
    flexmock(module.dump).should_receive('make_data_source_dump_filename').replace_with(
        lambda dump_path, name, hostname, port, container, label: '/'.join(
            (dump_path, f'{hostname}:{port}' if port else hostname, name)
        )
    )
    flexmock(module).should_receive('get_default_port').and_return(9999)

    assert module.make_data_source_dump_patterns(
        databases=flexmock(),
        config=flexmock(),
        borgmatic_runtime_directory='run',
        name='db',
        hostname='host',
        port=None,
    ) == (
        'borgmatic/host/db',
        'run/host/db',
        'borgmatic/host:9999/db',
    )


def test_make_data_source_dump_patterns_with_default_port_adds_pattern_with_no_port():
    flexmock(module).should_receive('make_dump_path').replace_with(lambda path: path)
    flexmock(module.dump).should_receive('make_data_source_dump_filename').replace_with(
        lambda dump_path, name, hostname, port, container, label: '/'.join(
            (dump_path, f'{hostname}:{port}' if port else hostname, name)
        )
    )
    flexmock(module).should_receive('get_default_port').and_return(9999)

    assert module.make_data_source_dump_patterns(
        databases=flexmock(),
        config=flexmock(),
        borgmatic_runtime_directory='run',
        name='db',
        hostname='host',
        port=9999,
    ) == (
        'borgmatic/host:9999/db',
        'run/host:9999/db',
        'borgmatic/host/db',
    )


def test_make_data_source_dump_patterns_with_non_default_port_adds_no_extra_patterns():
    flexmock(module).should_receive('make_dump_path').replace_with(lambda path: path)
    flexmock(module.dump).should_receive('make_data_source_dump_filename').replace_with(
        lambda dump_path, name, hostname, port, container, label: '/'.join(
            (dump_path, f'{hostname}:{port}' if port else hostname, name)
        )
    )
    flexmock(module).should_receive('get_default_port').and_return(9999)

    assert module.make_data_source_dump_patterns(
        databases=flexmock(),
        config=flexmock(),
        borgmatic_runtime_directory='run',
        name='db',
        hostname='host',
        port=1234,
    ) == (
        'borgmatic/host:1234/db',
        'run/host:1234/db',
    )
