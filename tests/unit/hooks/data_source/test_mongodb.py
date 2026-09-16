import logging

from flexmock import flexmock

from borgmatic.hooks.data_source import mongodb as module


def test_use_streaming_true_for_any_non_directory_format_databases():
    assert module.use_streaming(
        databases=[{'format': 'stuff'}, {'format': 'directory'}, {}],
        config=flexmock(),
    )


def test_use_streaming_false_for_all_directory_format_databases():
    assert not module.use_streaming(
        databases=[{'format': 'directory'}, {'format': 'directory'}],
        config=flexmock(),
    )


def test_use_streaming_false_for_no_databases():
    assert not module.use_streaming(databases=[], config=flexmock())


def test_make_password_config_file_pipe_writes_password_to_pipe():
    read_file_descriptor = 99
    write_file_descriptor = flexmock()

    flexmock(module.os).should_receive('pipe').and_return(
        (read_file_descriptor, write_file_descriptor),
    )
    flexmock(module.os).should_receive('write').with_args(
        write_file_descriptor,
        b'password: trustsome1',
    ).once()
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    assert module.make_password_config_file_pipe('trustsome1') == '/dev/fd/99'


def test_dump_data_sources_runs_mongodump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    ).and_return('databases/localhost/bar')
    flexmock(module).should_receive('make_password_config_file').and_return(flexmock())
    dump_commands = (flexmock(), flexmock())
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module).should_receive('build_dump_command').and_return(dump_commands[0]).and_return(
        dump_commands[1]
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/path/to/working/dir'
    )

    for (
        name,
        process,
        dump_command,
    ) in zip(('foo', 'bar'), processes, dump_commands):
        flexmock(module).should_receive('execute_command').with_args(
            dump_command,
            shell=True,
            run_to_completion=False,
            working_directory='/path/to/working/dir',
        ).and_return(process).once()

    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'mongodb_databases',
        [
            module.borgmatic.actions.restore.Dump('mongodb_databases', 'foo'),
            module.borgmatic.actions.restore.Dump('mongodb_databases', 'bar'),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/run/borgmatic/mongodb_databases',
            source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    ).once()

    assert (
        module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=False,
        )
        == processes
    )


def test_dump_data_sources_with_dry_run_skips_mongodump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    ).and_return('databases/localhost/bar')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module).should_receive('build_dump_command').and_return(flexmock())
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').never()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').never()

    assert (
        module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=True,
        )
        == []
    )


def test_dump_data_sources_runs_mongodump_with_directory_format():
    databases = [{'name': 'foo', 'format': 'directory'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    )
    flexmock(module).should_receive('make_password_config_file').and_return(flexmock())
    dump_command = flexmock()
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module).should_receive('build_dump_command').and_return(dump_command)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump').once()
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)

    flexmock(module).should_receive('execute_command').with_args(
        dump_command,
        shell=True,
        working_directory=None,
    ).and_return(flexmock()).once()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'mongodb_databases',
        [
            module.borgmatic.actions.restore.Dump('mongodb_databases', 'foo'),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/run/borgmatic/mongodb_databases',
            source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    ).once()

    assert (
        module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=False,
        )
        == []
    )


def test_dump_data_sources_dumps_all_databases():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/all',
    )
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(flexmock())
    flexmock(module).should_receive('make_password_config_file').and_return(flexmock())
    dump_command = flexmock()
    flexmock(module).should_receive('build_dump_command').and_return(dump_command)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)

    flexmock(module).should_receive('execute_command').with_args(
        dump_command,
        shell=True,
        run_to_completion=False,
        working_directory=None,
    ).and_return(process).once()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'mongodb_databases',
        [
            module.borgmatic.actions.restore.Dump('mongodb_databases', 'all'),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/run/borgmatic/mongodb_databases',
            source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    ).once()

    assert module.dump_data_sources(
        databases,
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    ) == [process]


def test_build_dump_command_with_username_injection_attack_gets_escaped():
    database = {'name': 'test', 'username': 'bob; naughty-command'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return('localhost')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('bob; naughty-command')

    command = module.build_dump_command(
        database, {}, '/path/to/password-config', dump_filename='test', dump_format='archive'
    )

    assert "'bob; naughty-command'" in command


def test_build_dump_command_uses_custom_mongodump_command():
    database = {
        'name': 'test',
        'hostname': 'localhost',
        'port': 27017,
        'username': 'user',
        'password': 'password',
        'mongodump_command': 'custom_mongodump',
        'options': '--gzip',
    }
    config = {}
    dump_filename = '/path/to/dump'
    dump_format = 'archive'
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return('localhost')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('user')

    command = module.build_dump_command(
        database, config, '/path/to/password-config', dump_filename, dump_format
    )

    assert command == (
        'custom_mongodump',
        '--host',
        'localhost',
        '--port',
        '27017',
        '--username',
        'user',
        '--config',
        '/path/to/password-config',
        '--db',
        'test',
        '--gzip',
        '--archive',
        '>',
        '/path/to/dump',
    )


def test_build_dump_command_prevents_shell_injection():
    database = {
        'name': 'testdb; rm -rf /',  # Malicious input
        'hostname': 'localhost',
        'port': 27017,
        'username': 'user',
        'password': 'password',
        'mongodump_command': 'mongodump',
        'options': '--gzip',
    }
    config = {}
    dump_filename = '/path/to/dump'
    dump_format = 'archive'
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return('localhost')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('user')

    command = module.build_dump_command(
        database, config, '/path/to/password-config', dump_filename, dump_format
    )

    # Ensure the malicious input is properly escaped and does not execute
    assert 'testdb; rm -rf /' not in command
    assert any(
        'testdb' in part for part in command
    )  # Check if 'testdb' is in any part of the tuple


def test_build_dump_command_includes_options():
    database = {'name': 'foo', 'options': '--stuff=such'}
    config = {}
    dump_filename = '/path/to/dump'
    dump_format = 'archive'
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_dump_command(
        database, config, '/path/to/password-config', dump_filename, dump_format
    )

    assert command == (
        'mongodump',
        '--config',
        '/path/to/password-config',
        '--db',
        'foo',
        '--stuff=such',
        '--archive',
        '>',
        '/path/to/dump',
    )


def test_build_dump_command_with_directory_format_uses_output_directory():
    database = {'name': 'foo', 'format': 'directory'}
    config = {}
    dump_filename = '/path/to/dump'
    dump_format = 'directory'
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_dump_command(
        database, config, '/path/to/password-config', dump_filename, dump_format
    )

    assert command == (
        'mongodump',
        '--out',
        '/path/to/dump',
        '--config',
        '/path/to/password-config',
        '--db',
        'foo',
    )


def test_build_dump_command_includes_username_and_password():
    database = {
        'name': 'foo',
        'username': 'mongo',
        'password': 'trustsome1',
        'authentication_database': 'admin',
    }
    config = {}
    dump_filename = '/path/to/dump'
    dump_format = 'archive'
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('mongo')

    command = module.build_dump_command(
        database, config, '/path/to/password-config', dump_filename, dump_format
    )

    assert command == (
        'mongodump',
        '--username',
        'mongo',
        '--config',
        '/path/to/password-config',
        '--authenticationDatabase',
        'admin',
        '--db',
        'foo',
        '--archive',
        '>',
        '/path/to/dump',
    )


def test_build_dump_command_includes_hostname_and_port():
    database = {'name': 'foo', 'hostname': 'database.example.org', 'port': 27018}
    config = {}
    dump_filename = '/path/to/dump'
    dump_format = 'archive'
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object
    ).and_return('database.example.org')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_dump_command(
        database, config, '/path/to/password-config', dump_filename, dump_format
    )

    assert command == (
        'mongodump',
        '--host',
        'database.example.org',
        '--port',
        '27018',
        '--config',
        '/path/to/password-config',
        '--db',
        'foo',
        '--archive',
        '>',
        '/path/to/dump',
    )


def test_make_data_source_dump_patterns_with_no_port_adds_pattern_with_default_port():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('.borgmatic')
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
        '.borgmatic/host/db',
        'borgmatic/host:9999/db',
    )


def test_make_data_source_dump_patterns_with_default_port_adds_pattern_with_no_port():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('.borgmatic')
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
        '.borgmatic/host:9999/db',
        'borgmatic/host/db',
    )


def test_make_data_source_dump_patterns_with_non_default_port_adds_no_extra_patterns():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('.borgmatic')
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
        '.borgmatic/host:1234/db',
    )


def test_restore_data_source_dump_runs_mongorestore():
    hook_config = [{'name': 'foo', 'schemas': None}, {'name': 'bar'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('make_password_config_file').and_return(flexmock())
    restore_command = flexmock()
    flexmock(module).should_receive('build_restore_command').and_return(restore_command)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        restore_command,
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        working_directory=None,
        borg_local_path='borg',
    ).and_yield().once()

    module.restore_data_source_dump(
        hook_config,
        {},
        data_source={'name': 'foo'},
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_runs_psql_for_all_database_dump():
    hook_config = [{'name': 'all', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('make_password_config_file').and_return(flexmock())
    restore_command = flexmock()
    flexmock(module).should_receive('build_restore_command').and_return(restore_command)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        restore_command,
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        working_directory=None,
        borg_local_path='borg',
    ).and_yield().once()

    module.restore_data_source_dump(
        hook_config,
        {},
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_with_dry_run_skips_restore():
    hook_config = [{'name': 'foo', 'schemas': None}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_data_source_dump(
        hook_config,
        {},
        data_source={'name': 'foo'},
        dry_run=True,
        extract_process=flexmock(),
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_build_restore_command_uses_custom_mongorestore_command():
    database = {
        'name': 'test',
        'restore_hostname': 'localhost',
        'restore_port': 27017,
        'restore_username': 'user',
        'restore_password': 'password',
        'mongorestore_command': 'custom_mongorestore',
        'restore_options': '--gzip',
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return('localhost')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(27017)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return('user')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('user')

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'custom_mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--host',
        'localhost',
        '--port',
        '27017',
        '--username',
        'user',
        '--config',
        '/path/to/password-config',
        '--gzip',
    ]


def test_build_restore_command_prevents_shell_injection():
    database = {
        'name': 'testdb; rm -rf /',  # Malicious input
        'restore_hostname': 'localhost',
        'restore_port': 27017,
        'restore_username': 'user',
        'restore_password': 'password',
        'mongorestore_command': 'mongorestore',
        'restore_options': '--gzip',
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return('localhost')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(27017)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return('user')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('password')

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    # Ensure the malicious input is properly escaped and does not execute
    assert 'rm -rf /' not in command
    assert ';' not in command


def test_build_restore_command_without_extract_process_makes_command_to_restore_from_disk():
    database = {
        'name': 'test',
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--config',
        '/path/to/password-config',
    ]


def test_build_restore_command_includes_schema_flags():
    database = {'name': 'foo', 'schemas': ['bar', 'baz']}
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--config',
        '/path/to/password-config',
        '--nsInclude',
        'bar',
        '--nsInclude',
        'baz',
    ]


def test_build_restore_command_includes_restore_options_as_flags():
    database = {
        'name': 'foo',
        'restore_options': '--harder',
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--config',
        '/path/to/password-config',
        '--harder',
    ]


def test_build_restore_command_without_connection_params_uses_restore_params_from_config():
    database = {
        'name': 'foo',
        'username': 'mongo',
        'password': 'trustsome1',
        'authentication_database': 'admin',
        'schemas': None,
        'restore_hostname': 'restorehost',
        'restore_port': 'restoreport',
        'restore_username': 'restoreuser',
        'restore_password': 'restorepass',
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return('restorehost')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return('restoreport')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return('restoreusername')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('restoreuser')

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--host',
        'restorehost',
        '--port',
        'restoreport',
        '--username',
        'restoreuser',
        '--config',
        '/path/to/password-config',
        '--authenticationDatabase',
        'admin',
    ]


def test_build_restore_command_with_connection_params_prefers_them_over_config():
    database = {
        'name': 'foo',
        'username': 'mongo',
        'password': 'trustsome1',
        'authentication_database': 'admin',
        'restore_hostname': 'restorehost',
        'restore_port': 'restoreport',
        'restore_username': 'restoreusername',
        'restore_password': 'restorepassword',
        'schemas': None,
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': 'clihost',
        'port': 'cliport',
        'username': 'cliusername',
        'password': 'clipassword',
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return('clihost')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return('cliport')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return('cliusername')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('cliusername')

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--host',
        'clihost',
        '--port',
        'cliport',
        '--username',
        'cliusername',
        '--config',
        '/path/to/password-config',
        '--authenticationDatabase',
        'admin',
    ]


def test_build_restore_command_includes_username_and_password():
    database = {
        'name': 'foo',
        'username': 'mongo',
        'password': 'trustsome1',
        'authentication_database': 'admin',
    }
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(None)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return('mongo')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return('mongo')

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--username',
        'mongo',
        '--config',
        '/path/to/password-config',
        '--authenticationDatabase',
        'admin',
    ]


def test_build_restore_command_includes_hostname_and_port():
    database = {'name': 'foo', 'hostname': 'database.example.org', 'port': 27018, 'schemas': None}
    config = {}
    dump_filename = '/path/to/dump'
    connection_params = {
        'hostname': None,
        'port': None,
        'username': None,
        'password': None,
    }
    extract_process = None
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'hostname', object, object, True
    ).and_return('database.example.org')
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'port', object, object, True
    ).and_return(27018)
    flexmock(module.database_config).should_receive('resolve_database_option').with_args(
        'username', object, object, True
    ).and_return(None)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        '/path/to/password-config',
        dump_filename,
        connection_params,
    )

    assert command == [
        'mongorestore',
        '--dir',
        '/path/to/dump',
        '--drop',
        '--host',
        'database.example.org',
        '--port',
        '27018',
        '--config',
        '/path/to/password-config',
    ]
