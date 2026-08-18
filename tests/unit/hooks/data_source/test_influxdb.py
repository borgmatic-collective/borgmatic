from flexmock import flexmock

from borgmatic.hooks.data_source import influxdb as module


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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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


def test_build_dump_command_with_tls_disabled():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'tls': False,  # HTTP instead of HTTPS
        'password': 'testtoken',
        'organization_id': 'ccf6258c1e195e27',
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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


def test_build_dump_command_with_no_port_uses_default_port():
    database = {
        'hostname': 'myexample.com',
        'password': 'testtoken',
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module).should_receive('get_default_port').and_return(9999)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:9999',
        '--token',
        'testtoken',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_skip_verify_flag():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'skip_verify': True,
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--skip-verify',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

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


def test_build_dump_command_with_compression():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'compression': 'none',
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '--compression',
        'none',
        '/tmp/dumpfile',
    )


def test_build_dump_command_resolves_password_credential():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': '{credential file /path/to/token}',
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).with_args('{credential file /path/to/token}', {}).and_return('resolvedtoken').once()

    command = module.build_dump_command(database, {}, dump_filename)

    assert command == (
        'influx',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'resolvedtoken',
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
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

    assert command == (
        '/usr/local/bin/influx2',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '/tmp/dumpfile',
    )


def test_build_dump_command_with_influx_command_containing_spaces():
    database = {
        'hostname': 'myexample.com',
        'port': 8086,
        'password': 'testtoken',
        'influx_command': '"/usr/local/my influx/influx" --skip-verify',
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename)

    # The command is not shell quoted, as it doesn't get run within a shell.
    assert command == (
        '/usr/local/my influx/influx',
        '--skip-verify',
        'backup',
        '--host',
        'https://myexample.com:8086',
        '--token',
        'testtoken',
        '/tmp/dumpfile',
    )


def test_dump_data_sources_dumps_each_database():
    databases = [
        {
            'name': 'influx-backup',
            # hostname defaults to 'localhost'
            'port': 8086,
            'password': 'mytoken',
            'organization_id': 'org123',
            'label': 'mylabel',
        },
        {
            'name': 'other-backup',
            'hostname': 'influx.example.org',
            'port': 8087,
        },
    ]
    commands = (flexmock(), flexmock())
    patterns = []
    flexmock(module.dump).should_receive('make_data_source_dump_filename').with_args(
        '/tmp/influxdb_databases',
        'influx-backup',
        hostname=None,
        port=8086,
        label='mylabel',
    ).and_return('/tmp/dumpfile').once()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').with_args(
        '/tmp/influxdb_databases',
        'other-backup',
        hostname='influx.example.org',
        port=8087,
        label=None,
    ).and_return('/tmp/other_dumpfile').once()
    flexmock(module.dump).should_receive('create_parent_directory_for_dump').twice()

    for database, command in zip(databases, commands):
        flexmock(module).should_receive('build_dump_command').with_args(
            database, {}, object
        ).and_return(command).once()
        flexmock(module).should_receive('execute_command').with_args(command).once()

    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/tmp',
        'influxdb_databases',
        [
            module.borgmatic.actions.restore.Dump(
                'influxdb_databases', 'influx-backup', None, 8086, 'mylabel'
            ),
            module.borgmatic.actions.restore.Dump(
                'influxdb_databases', 'other-backup', 'influx.example.org', 8087, None
            ),
        ],
    ).once()

    # No subprocess.Popen instances are returned.
    assert (
        module.dump_data_sources(
            databases,
            config={},
            config_paths=[],
            borgmatic_runtime_directory='/tmp',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        module.borgmatic.borg.pattern.Pattern('/tmp/influxdb_databases'),
        module.borgmatic.borg.pattern.Pattern(
            '/tmp/influxdb_databases',
            type=module.borgmatic.borg.pattern.Pattern_type.INCLUDE,
        ),
    ]


def test_dump_data_sources_with_dry_run_skips_command_execution():
    databases = [{'name': 'influx-backup', 'hostname': 'localhost', 'password': 'mytoken'}]
    patterns = []
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/tmp/dumpfile'
    )
    flexmock(module.dump).should_receive('create_parent_directory_for_dump').never()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').never()

    assert (
        module.dump_data_sources(
            databases,
            config={},
            config_paths=[],
            borgmatic_runtime_directory='/tmp',
            patterns=patterns,
            dry_run=True,
        )
        == []
    )

    assert patterns == []


def test_restore_data_source_dump_executes_restore_command():
    data_source = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': 8086,
        'password': 'mytoken',
        'organization_id': 'org123',
        'label': 'mylabel',
    }
    connection_params = {
        'hostname': 'localhost',
        'port': 8086,
        'password': 'mytoken',
    }
    restore_command = flexmock()

    flexmock(module.dump).should_receive('make_data_source_dump_filename').with_args(
        '/tmp/influxdb_databases',
        'influx-backup',
        hostname='localhost',
        port=8086,
        label='mylabel',
    ).and_return('/tmp/dumpfile')
    flexmock(module).should_receive('build_restore_command').with_args(
        data_source, {}, '/tmp/dumpfile', connection_params
    ).and_return(restore_command).once()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    # There's no extract process to consume, as this hook restores from a dump directory.
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        restore_command,
        [],
        output_log_level=module.logging.DEBUG,
        working_directory='/working',
        borg_local_path='borg',
    ).and_yield().once()

    module.restore_data_source_dump(
        hook_config={},
        config={},
        data_source=data_source,
        dry_run=False,
        extract_process=None,
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
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/tmp/dumpfile'
    )
    flexmock(module).should_receive('build_restore_command').and_return(flexmock())
    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_data_source_dump(
        hook_config={},
        config={},
        data_source=data_source,
        dry_run=True,
        extract_process=None,
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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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
        'password': 'restoretoken',
    }
    dump_filename = '/tmp/dumpfile'

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

    # The connection parameters take precedence over the database values.
    assert command == (
        'influx',
        'restore',
        '--host',
        'https://restorehost:9999',
        '--token',
        'restoretoken',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_no_port_uses_default_port():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'password': 'mytoken',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'

    flexmock(module).should_receive('get_default_port').and_return(9999)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:9999',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_with_tls_disabled():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': 8086,
        'tls': False,  # HTTP instead of HTTPS
        'password': 'mytoken',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

    assert command == (
        'influx',
        'restore',
        '--host',
        'http://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
        '/tmp/dumpfile',
    )


def test_build_restore_command_resolves_password_credential():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',
        'password': '{credential file /path/to/token}',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).with_args('{credential file /path/to/token}', {}).and_return('resolvedtoken').once()

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

    assert command == (
        'influx',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'resolvedtoken',
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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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


def test_build_restore_command_with_influx_command_containing_spaces():
    database = {
        'name': 'influx-backup',
        'hostname': 'localhost',
        'port': '8086',  # Changed to string to avoid TypeError
        'password': 'mytoken',
        'influx_command': '"/usr/local/my influx/influx" --skip-verify',
    }
    connection_params = {
        'hostname': None,
        'port': None,
        'password': None,
    }
    dump_filename = '/tmp/dumpfile'

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

    # The command is not shell quoted, as it doesn't get run within a shell.
    assert command == (
        '/usr/local/my influx/influx',
        '--skip-verify',
        'restore',
        '--host',
        'https://localhost:8086',
        '--token',
        'mytoken',
        '--bucket',
        'influx-backup',
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

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_restore_command(database, {}, dump_filename, connection_params)

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
