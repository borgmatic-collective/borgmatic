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


def test_dump_data_sources_runs_mongodump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    ).and_return('databases/localhost/bar')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_command').with_args(
            ('mongodump', '--db', name, '--archive', '>', f'databases/localhost/{name}'),
            shell=True,
            run_to_completion=False,
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


def test_dump_data_sources_runs_mongodump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 27018}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/database.example.org/foo',
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mongodump',
            '--host',
            'database.example.org',
            '--port',
            '27018',
            '--db',
            'foo',
            '--archive',
            '>',
            'databases/database.example.org/foo',
        ),
        shell=True,
        run_to_completion=False,
    ).and_return(process).once()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'mongodb_databases',
        [
            module.borgmatic.actions.restore.Dump(
                'mongodb_databases', 'foo', 'database.example.org', 27018
            ),
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


def test_dump_data_sources_runs_mongodump_with_username_and_password():
    databases = [
        {
            'name': 'foo',
            'username': 'mongo',
            'password': 'trustsome1',
            'authentication_database': 'admin',
        },
    ]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    )
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('make_password_config_file').with_args('trustsome1').and_return(
        '/dev/fd/99',
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mongodump',
            '--username',
            'mongo',
            '--config',
            '/dev/fd/99',
            '--authenticationDatabase',
            'admin',
            '--db',
            'foo',
            '--archive',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        run_to_completion=False,
    ).and_return(process).once()
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

    assert module.dump_data_sources(
        databases,
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_runs_mongodump_with_directory_format():
    databases = [{'name': 'foo', 'format': 'directory'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    )
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()

    flexmock(module).should_receive('execute_command').with_args(
        ('mongodump', '--out', 'databases/localhost/foo', '--db', 'foo'),
        shell=True,
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


def test_dump_data_sources_runs_mongodump_with_options():
    databases = [{'name': 'foo', 'options': '--stuff=such'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mongodump',
            '--db',
            'foo',
            '--stuff=such',
            '--archive',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        run_to_completion=False,
    ).and_return(process).once()
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

    assert module.dump_data_sources(
        databases,
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_runs_mongodumpall_for_all_databases():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/all',
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('mongodump', '--archive', '>', 'databases/localhost/all'),
        shell=True,
        run_to_completion=False,
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


def test_make_password_config_file_writes_password_to_pipe():
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

    assert module.make_password_config_file('trustsome1') == '/dev/fd/99'


def test_build_dump_command_with_username_injection_attack_gets_escaped():
    database = {'name': 'test', 'username': 'bob; naughty-command'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)

    command = module.build_dump_command(database, {}, dump_filename='test', dump_format='archive')

    assert "'bob; naughty-command'" in command


def test_restore_data_source_dump_runs_mongorestore():
    hook_config = [{'name': 'foo', 'schemas': None}, {'name': 'bar'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--archive', '--drop'],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_data_source_dump_runs_mongorestore_with_hostname_and_port():
    hook_config = [
        {'name': 'foo', 'hostname': 'database.example.org', 'port': 27018, 'schemas': None},
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--host',
            'database.example.org',
            '--port',
            '27018',
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_data_source_dump_runs_mongorestore_with_username_and_password():
    hook_config = [
        {
            'name': 'foo',
            'username': 'mongo',
            'password': 'trustsome1',
            'authentication_database': 'admin',
            'schemas': None,
        },
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('make_password_config_file').with_args('trustsome1').and_return(
        '/dev/fd/99',
    )
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--username',
            'mongo',
            '--config',
            '/dev/fd/99',
            '--authenticationDatabase',
            'admin',
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_data_source_dump_with_connection_params_uses_connection_params_for_restore():
    hook_config = [
        {
            'name': 'foo',
            'username': 'mongo',
            'password': 'trustsome1',
            'authentication_database': 'admin',
            'restore_hostname': 'restorehost',
            'restore_port': 'restoreport',
            'restore_username': 'restoreusername',
            'restore_password': 'restorepassword',
            'schemas': None,
        },
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('make_password_config_file').with_args(
        'clipassword',
    ).and_return('/dev/fd/99')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--host',
            'clihost',
            '--port',
            'cliport',
            '--username',
            'cliusername',
            '--config',
            '/dev/fd/99',
            '--authenticationDatabase',
            'admin',
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': 'clihost',
            'port': 'cliport',
            'username': 'cliusername',
            'password': 'clipassword',
        },
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_without_connection_params_uses_restore_params_in_config_for_restore():
    hook_config = [
        {
            'name': 'foo',
            'username': 'mongo',
            'password': 'trustsome1',
            'authentication_database': 'admin',
            'schemas': None,
            'restore_hostname': 'restorehost',
            'restore_port': 'restoreport',
            'restore_username': 'restoreuser',
            'restore_password': 'restorepass',
        },
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('make_password_config_file').with_args(
        'restorepass',
    ).and_return('/dev/fd/99')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--host',
            'restorehost',
            '--port',
            'restoreport',
            '--username',
            'restoreuser',
            '--config',
            '/dev/fd/99',
            '--authenticationDatabase',
            'admin',
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_data_source_dump_runs_mongorestore_with_options():
    hook_config = [{'name': 'foo', 'restore_options': '--harder', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--archive', '--drop', '--harder'],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_databases_dump_runs_mongorestore_with_schemas():
    hook_config = [{'name': 'foo', 'schemas': ['bar', 'baz']}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--nsInclude',
            'bar',
            '--nsInclude',
            'baz',
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_data_source_dump_runs_psql_for_all_database_dump():
    hook_config = [{'name': 'all', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--archive'],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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


def test_restore_data_source_dump_without_extract_process_restores_from_disk():
    hook_config = [{'name': 'foo', 'format': 'directory', 'schemas': None}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('/dump/path')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--dir', '/dump/path', '--drop'],
        processes=[],
        output_log_level=logging.DEBUG,
        input_file=None,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        data_source={'name': 'foo'},
        dry_run=False,
        extract_process=None,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_dump_data_sources_uses_custom_mongodump_command():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock(),
    )
    databases = [{'name': 'foo', 'mongodump_command': 'custom_mongodump'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo',
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'custom_mongodump',
            '--db',
            'foo',
            '--archive',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        run_to_completion=False,
    ).and_return(process).once()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'mongodb_databases',
        [
            module.borgmatic.actions.restore.Dump('mongodb_databases', 'foo'),
        ],
    ).once()

    assert module.dump_data_sources(
        databases,
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    ) == [process]


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

    command = module.build_dump_command(database, config, dump_filename, dump_format)

    # Ensure the malicious input is properly escaped and does not execute
    assert 'testdb; rm -rf /' not in command
    assert any(
        'testdb' in part for part in command
    )  # Check if 'testdb' is in any part of the tuple


def test_restore_data_source_dump_uses_custom_mongorestore_command():
    hook_config = [
        {
            'name': 'foo',
            'mongorestore_command': 'custom_mongorestore',
            'schemas': None,
            'restore_options': '--gzip',
        },
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'custom_mongorestore',  # Should use custom command instead of default
            '--archive',
            '--drop',
            '--gzip',  # Should include restore options
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

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

    command = module.build_restore_command(
        extract_process,
        database,
        config,
        dump_filename,
        connection_params,
    )

    # Ensure the malicious input is properly escaped and does not execute
    assert 'rm -rf /' not in command
    assert ';' not in command
