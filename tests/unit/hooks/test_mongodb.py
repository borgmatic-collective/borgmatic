import logging

from flexmock import flexmock

from borgmatic.hooks import mongodb as module


def test_dump_data_sources_runs_mongodump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_command').with_args(
            ('mongodump', '--db', name, '--archive', '>', f'databases/localhost/{name}'),
            shell=True,
            run_to_completion=False,
        ).and_return(process).once()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == processes


def test_dump_data_sources_with_dry_run_skips_mongodump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=True) == []


def test_dump_data_sources_runs_mongodump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/database.example.org/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mongodump',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--db',
            'foo',
            '--archive',
            '>',
            'databases/database.example.org/foo',
        ),
        shell=True,
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == [process]


def test_dump_data_sources_runs_mongodump_with_username_and_password():
    databases = [
        {
            'name': 'foo',
            'username': 'mongo',
            'password': 'trustsome1',
            'authentication_database': 'admin',
        }
    ]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mongodump',
            '--username',
            'mongo',
            '--password',
            'trustsome1',
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

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == [process]


def test_dump_data_sources_runs_mongodump_with_directory_format():
    databases = [{'name': 'foo', 'format': 'directory'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()

    flexmock(module).should_receive('execute_command').with_args(
        ('mongodump', '--out', 'databases/localhost/foo', '--db', 'foo'),
        shell=True,
    ).and_return(flexmock()).once()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == []


def test_dump_data_sources_runs_mongodump_with_options():
    databases = [{'name': 'foo', 'options': '--stuff=such'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
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

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == [process]


def test_dump_data_sources_runs_mongodumpall_for_all_databases():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('mongodump', '--archive', '>', 'databases/localhost/all'),
        shell=True,
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(databases, {}, 'test.yaml', dry_run=False) == [process]


def test_build_dump_command_with_username_injection_attack_gets_escaped():
    database = {'name': 'test', 'username': 'bob; naughty-command'}

    command = module.build_dump_command(database, dump_filename='test', dump_format='archive')

    assert "'bob; naughty-command'" in command


def test_restore_data_source_dump_runs_mongorestore():
    hook_config = [{'name': 'foo', 'schemas': None}, {'name': 'bar'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--archive', '--drop'],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'foo'},
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_data_source_dump_runs_mongorestore_with_hostname_and_port():
    hook_config = [
        {'name': 'foo', 'hostname': 'database.example.org', 'port': 5433, 'schemas': None}
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--host',
            'database.example.org',
            '--port',
            '5433',
        ],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_data_source_dump_runs_mongorestore_with_username_and_password():
    hook_config = [
        {
            'name': 'foo',
            'username': 'mongo',
            'password': 'trustsome1',
            'authentication_database': 'admin',
            'schemas': None,
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        [
            'mongorestore',
            '--archive',
            '--drop',
            '--username',
            'mongo',
            '--password',
            'trustsome1',
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
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
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
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
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
            '--password',
            'clipassword',
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
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': 'clihost',
            'port': 'cliport',
            'username': 'cliusername',
            'password': 'clipassword',
        },
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
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
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
            '--password',
            'restorepass',
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
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_data_source_dump_runs_mongorestore_with_options():
    hook_config = [{'name': 'foo', 'restore_options': '--harder', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--archive', '--drop', '--harder'],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_databases_dump_runs_mongorestore_with_schemas():
    hook_config = [{'name': 'foo', 'schemas': ['bar', 'baz']}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
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
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_data_source_dump_runs_psql_for_all_database_dump():
    hook_config = [{'name': 'all', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--archive'],
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source=hook_config[0],
        dry_run=False,
        extract_process=extract_process,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_data_source_dump_with_dry_run_skips_restore():
    hook_config = [{'name': 'foo', 'schemas': None}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'foo'},
        dry_run=True,
        extract_process=flexmock(),
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )


def test_restore_data_source_dump_without_extract_process_restores_from_disk():
    hook_config = [{'name': 'foo', 'format': 'directory', 'schemas': None}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('/dump/path')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ['mongorestore', '--dir', '/dump/path', '--drop'],
        processes=[],
        output_log_level=logging.DEBUG,
        input_file=None,
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'foo'},
        dry_run=False,
        extract_process=None,
        connection_params={
            'hostname': None,
            'port': None,
            'username': None,
            'password': None,
        },
    )
