import logging

import pytest
from flexmock import flexmock

from borgmatic.hooks import postgresql as module


def test_make_extra_environment_maps_options_to_environment():
    database = {
        'name': 'foo',
        'password': 'pass',
        'ssl_mode': 'require',
        'ssl_cert': 'cert.crt',
        'ssl_key': 'key.key',
        'ssl_root_cert': 'root.crt',
        'ssl_crl': 'crl.crl',
    }
    expected = {
        'PGPASSWORD': 'pass',
        'PGSSLMODE': 'require',
        'PGSSLCERT': 'cert.crt',
        'PGSSLKEY': 'key.key',
        'PGSSLROOTCERT': 'root.crt',
        'PGSSLCRL': 'crl.crl',
    }

    extra_env = module.make_extra_environment(database)

    assert extra_env == expected


def test_make_extra_environment_with_cli_password_sets_correct_password():
    database = {'name': 'foo', 'restore_password': 'trustsome1', 'password': 'anotherpassword'}

    extra = module.make_extra_environment(
        database, restore_connection_params={'password': 'clipassword'}
    )

    assert extra['PGPASSWORD'] == 'clipassword'


def test_make_extra_environment_without_cli_password_or_configured_password_does_not_set_password():
    database = {'name': 'foo'}

    extra = module.make_extra_environment(
        database, restore_connection_params={'username': 'someone'}
    )

    assert 'PGPASSWORD' not in extra


def test_make_extra_environment_without_ssl_mode_does_not_set_ssl_mode():
    database = {'name': 'foo'}

    extra = module.make_extra_environment(database)

    assert 'PGSSLMODE' not in extra


def test_database_names_to_dump_passes_through_individual_database_name():
    database = {'name': 'foo'}

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
    )


def test_database_names_to_dump_passes_through_individual_database_name_with_format():
    database = {'name': 'foo', 'format': 'custom'}

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
    )


def test_database_names_to_dump_passes_through_all_without_format():
    database = {'name': 'all'}

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'all',
    )


def test_database_names_to_dump_with_all_and_format_and_dry_run_bails():
    database = {'name': 'all', 'format': 'custom'}
    flexmock(module).should_receive('execute_command_and_capture_output').never()

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=True) == ()


def test_database_names_to_dump_with_all_and_format_lists_databases():
    database = {'name': 'all', 'format': 'custom'}
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        'foo,test,\nbar,test,"stuff and such"'
    )

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
        'bar',
    )


def test_database_names_to_dump_with_all_and_format_lists_databases_with_hostname_and_port():
    database = {'name': 'all', 'format': 'custom', 'hostname': 'localhost', 'port': 1234}
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'psql',
            '--list',
            '--no-password',
            '--no-psqlrc',
            '--csv',
            '--tuples-only',
            '--host',
            'localhost',
            '--port',
            '1234',
        ),
        extra_environment=object,
    ).and_return('foo,test,\nbar,test,"stuff and such"')

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
        'bar',
    )


def test_database_names_to_dump_with_all_and_format_lists_databases_with_username():
    database = {'name': 'all', 'format': 'custom', 'username': 'postgres'}
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'psql',
            '--list',
            '--no-password',
            '--no-psqlrc',
            '--csv',
            '--tuples-only',
            '--username',
            'postgres',
        ),
        extra_environment=object,
    ).and_return('foo,test,\nbar,test,"stuff and such"')

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
        'bar',
    )


def test_database_names_to_dump_with_all_and_format_lists_databases_with_options():
    database = {'name': 'all', 'format': 'custom', 'list_options': '--harder'}
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('psql', '--list', '--no-password', '--no-psqlrc', '--csv', '--tuples-only', '--harder'),
        extra_environment=object,
    ).and_return('foo,test,\nbar,test,"stuff and such"')

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
        'bar',
    )


def test_database_names_to_dump_with_all_and_format_excludes_particular_databases():
    database = {'name': 'all', 'format': 'custom'}
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        'foo,test,\ntemplate0,test,blah'
    )

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
    )


def test_database_names_to_dump_with_all_and_psql_command_uses_custom_command():
    database = {
        'name': 'all',
        'format': 'custom',
        'psql_command': 'docker exec --workdir * mycontainer psql',
    }
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'docker',
            'exec',
            '--workdir',
            "'*'",  # Should get shell escaped to prevent injection attacks.
            'mycontainer',
            'psql',
            '--list',
            '--no-password',
            '--no-psqlrc',
            '--csv',
            '--tuples-only',
        ),
        extra_environment=object,
    ).and_return('foo,text').once()

    assert module.database_names_to_dump(database, flexmock(), flexmock(), dry_run=False) == (
        'foo',
    )


def test_use_streaming_true_for_any_non_directory_format_databases():
    assert module.use_streaming(
        databases=[{'format': 'stuff'}, {'format': 'directory'}, {}],
        config=flexmock(),
        log_prefix=flexmock(),
    )


def test_use_streaming_false_for_all_directory_format_databases():
    assert not module.use_streaming(
        databases=[{'format': 'directory'}, {'format': 'directory'}],
        config=flexmock(),
        log_prefix=flexmock(),
    )


def test_use_streaming_false_for_no_databases():
    assert not module.use_streaming(databases=[], config=flexmock(), log_prefix=flexmock())


def test_dump_data_sources_runs_pg_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_command').with_args(
            (
                'pg_dump',
                '--no-password',
                '--clean',
                '--if-exists',
                '--format',
                'custom',
                name,
                '>',
                f'databases/localhost/{name}',
            ),
            shell=True,
            extra_environment={'PGSSLMODE': 'disable'},
            run_to_completion=False,
        ).and_return(process).once()

    assert (
        module.dump_data_sources(
            databases,
            {},
            'test.yaml',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=[],
            dry_run=False,
        )
        == processes
    )


def test_dump_data_sources_raises_when_no_database_names_to_dump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(())

    with pytest.raises(ValueError):
        module.dump_data_sources(
            databases,
            {},
            'test.yaml',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=[],
            dry_run=False,
        )


def test_dump_data_sources_does_not_raise_when_no_database_names_to_dump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(())

    module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=True,
    ) == []


def test_dump_data_sources_with_duplicate_dump_skips_pg_dump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert (
        module.dump_data_sources(
            databases,
            {},
            'test.yaml',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=[],
            dry_run=False,
        )
        == []
    )


def test_dump_data_sources_with_dry_run_skips_pg_dump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert (
        module.dump_data_sources(
            databases,
            {},
            'test.yaml',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=[],
            dry_run=True,
        )
        == []
    )


def test_dump_data_sources_runs_pg_dump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    process = flexmock()
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/database.example.org/foo'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--format',
            'custom',
            'foo',
            '>',
            'databases/database.example.org/foo',
        ),
        shell=True,
        extra_environment={'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_runs_pg_dump_with_username_and_password():
    databases = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    process = flexmock()
    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'}
    )
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--username',
            'postgres',
            '--format',
            'custom',
            'foo',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        extra_environment={'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_with_username_injection_attack_gets_escaped():
    databases = [{'name': 'foo', 'username': 'postgres; naughty-command', 'password': 'trustsome1'}]
    process = flexmock()
    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'}
    )
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--username',
            "'postgres; naughty-command'",
            '--format',
            'custom',
            'foo',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        extra_environment={'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_runs_pg_dump_with_directory_format():
    databases = [{'name': 'foo', 'format': 'directory'}]
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--format',
            'directory',
            '--file',
            'databases/localhost/foo',
            'foo',
        ),
        shell=True,
        extra_environment={'PGSSLMODE': 'disable'},
    ).and_return(flexmock()).once()

    assert (
        module.dump_data_sources(
            databases,
            {},
            'test.yaml',
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            source_directories=[],
            dry_run=False,
        )
        == []
    )


def test_dump_data_sources_runs_pg_dump_with_options():
    databases = [{'name': 'foo', 'options': '--stuff=such'}]
    process = flexmock()
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--format',
            'custom',
            '--stuff=such',
            'foo',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        extra_environment={'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_runs_pg_dumpall_for_all_databases():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('all',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('pg_dumpall', '--no-password', '--clean', '--if-exists', '>', 'databases/localhost/all'),
        shell=True,
        extra_environment={'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_runs_non_default_pg_dump():
    databases = [{'name': 'foo', 'pg_dump_command': 'special_pg_dump --compress *'}]
    process = flexmock()
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',))
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'special_pg_dump',
            '--compress',
            "'*'",  # Should get shell escaped to prevent injection attacks.
            '--no-password',
            '--clean',
            '--if-exists',
            '--format',
            'custom',
            'foo',
            '>',
            'databases/localhost/foo',
        ),
        shell=True,
        extra_environment={'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        'test.yaml',
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        source_directories=[],
        dry_run=False,
    ) == [process]


def test_restore_data_source_dump_runs_pg_restore():
    hook_config = [{'name': 'foo', 'schemas': None}, {'name': 'bar'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_runs_pg_restore_with_hostname_and_port():
    hook_config = [
        {'name': 'foo', 'hostname': 'database.example.org', 'port': 5433, 'schemas': None}
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '--host',
            'database.example.org',
            '--port',
            '5433',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_runs_pg_restore_with_username_and_password():
    hook_config = [
        {'name': 'foo', 'username': 'postgres', 'password': 'trustsome1', 'schemas': None}
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'}
    )
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '--username',
            'postgres',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--username',
            'postgres',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_with_connection_params_uses_connection_params_for_restore():
    hook_config = [
        {
            'name': 'foo',
            'hostname': 'database.example.org',
            'port': 5433,
            'username': 'postgres',
            'password': 'trustsome1',
            'restore_hostname': 'restorehost',
            'restore_port': 'restoreport',
            'restore_username': 'restoreusername',
            'restore_password': 'restorepassword',
            'schemas': None,
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'clipassword', 'PGSSLMODE': 'disable'}
    )
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '--host',
            'clihost',
            '--port',
            'cliport',
            '--username',
            'cliusername',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGPASSWORD': 'clipassword', 'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--host',
            'clihost',
            '--port',
            'cliport',
            '--username',
            'cliusername',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGPASSWORD': 'clipassword', 'PGSSLMODE': 'disable'},
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'foo'},
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
            'hostname': 'database.example.org',
            'port': 5433,
            'username': 'postgres',
            'password': 'trustsome1',
            'schemas': None,
            'restore_hostname': 'restorehost',
            'restore_port': 'restoreport',
            'restore_username': 'restoreusername',
            'restore_password': 'restorepassword',
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'restorepassword', 'PGSSLMODE': 'disable'}
    )
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '--host',
            'restorehost',
            '--port',
            'restoreport',
            '--username',
            'restoreusername',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGPASSWORD': 'restorepassword', 'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--host',
            'restorehost',
            '--port',
            'restoreport',
            '--username',
            'restoreusername',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGPASSWORD': 'restorepassword', 'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_runs_pg_restore_with_options():
    hook_config = [
        {
            'name': 'foo',
            'restore_options': '--harder',
            'analyze_options': '--smarter',
            'schemas': None,
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '--harder',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--dbname',
            'foo',
            '--smarter',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_runs_psql_for_all_database_dump():
    hook_config = [{'name': 'all', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('psql', '--no-password', '--no-psqlrc', '--quiet', '--command', 'ANALYZE'),
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source={'name': 'all'},
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


def test_restore_data_source_dump_runs_psql_for_plain_database_dump():
    hook_config = [{'name': 'foo', 'format': 'plain', 'schemas': None}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('psql', '--no-password', '--no-psqlrc', '--dbname', 'foo'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_runs_non_default_pg_restore_and_psql():
    hook_config = [
        {
            'name': 'foo',
            'pg_restore_command': 'docker exec --workdir * mycontainer pg_restore',
            'psql_command': 'docker exec --workdir * mycontainer psql',
            'schemas': None,
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'docker',
            'exec',
            '--workdir',
            "'*'",  # Should get shell escaped to prevent injection attacks.
            'mycontainer',
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'docker',
            'exec',
            '--workdir',
            "'*'",  # Should get shell escaped to prevent injection attacks.
            'mycontainer',
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_with_dry_run_skips_restore():
    hook_config = [{'name': 'foo', 'schemas': None}]

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_without_extract_process_restores_from_disk():
    hook_config = [{'name': 'foo', 'schemas': None}]

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('/dump/path')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '/dump/path',
        ),
        processes=[],
        output_log_level=logging.DEBUG,
        input_file=None,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
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
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_with_schemas_restores_schemas():
    hook_config = [{'name': 'foo', 'schemas': ['bar', 'baz']}]

    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('/dump/path')
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'pg_restore',
            '--no-password',
            '--if-exists',
            '--exit-on-error',
            '--clean',
            '--dbname',
            'foo',
            '/dump/path',
            '--schema',
            'bar',
            '--schema',
            'baz',
        ),
        processes=[],
        output_log_level=logging.DEBUG,
        input_file=None,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--no-psqlrc',
            '--quiet',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()

    module.restore_data_source_dump(
        hook_config,
        {},
        'test.yaml',
        data_source=hook_config[0],
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
