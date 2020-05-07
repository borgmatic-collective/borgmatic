import pytest
from flexmock import flexmock

from borgmatic.hooks import postgresql as module


def test_dump_databases_runs_pg_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_command').with_args(
            (
                'pg_dump',
                '--no-password',
                '--clean',
                '--if-exists',
                '--no-sync',
                '--file',
                'databases/localhost/{}'.format(name),
                '--format',
                'custom',
                name,
            ),
            extra_environment=None,
            run_to_completion=False,
        ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == processes


def test_dump_databases_with_dry_run_skips_pg_dump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=True) == []


def test_dump_databases_runs_pg_dump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/database.example.org/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--no-sync',
            '--file',
            'databases/database.example.org/foo',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--format',
            'custom',
            'foo',
        ),
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_runs_pg_dump_with_username_and_password():
    databases = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--no-sync',
            '--file',
            'databases/localhost/foo',
            '--username',
            'postgres',
            '--format',
            'custom',
            'foo',
        ),
        extra_environment={'PGPASSWORD': 'trustsome1'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_runs_pg_dump_with_format():
    databases = [{'name': 'foo', 'format': 'tar'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--no-sync',
            '--file',
            'databases/localhost/foo',
            '--format',
            'tar',
            'foo',
        ),
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_runs_pg_dump_with_options():
    databases = [{'name': 'foo', 'options': '--stuff=such'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--if-exists',
            '--no-sync',
            '--file',
            'databases/localhost/foo',
            '--format',
            'custom',
            '--stuff=such',
            'foo',
        ),
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_runs_pg_dumpall_for_all_databases():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dumpall',
            '--no-password',
            '--clean',
            '--if-exists',
            '--no-sync',
            '--file',
            'databases/localhost/all',
        ),
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_restore_database_dump_runs_pg_restore():
    database_config = [{'name': 'foo'}]
    extract_process = flexmock(stdout=flexmock())

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
        input_file=extract_process.stdout,
        extra_environment=None,
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('psql', '--no-password', '--quiet', '--dbname', 'foo', '--command', 'ANALYZE'),
        extra_environment=None,
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_errors_on_multiple_database_config():
    database_config = [{'name': 'foo'}, {'name': 'bar'}]

    flexmock(module).should_receive('execute_command_with_processes').never()
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.restore_database_dump(
            database_config, 'test.yaml', {}, dry_run=False, extract_process=flexmock()
        )


def test_restore_database_dump_runs_pg_restore_with_hostname_and_port():
    database_config = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    extract_process = flexmock(stdout=flexmock())

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
        input_file=extract_process.stdout,
        extra_environment=None,
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
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
        extra_environment=None,
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_runs_pg_restore_with_username_and_password():
    database_config = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    extract_process = flexmock(stdout=flexmock())

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
        input_file=extract_process.stdout,
        extra_environment={'PGPASSWORD': 'trustsome1'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        (
            'psql',
            '--no-password',
            '--quiet',
            '--username',
            'postgres',
            '--dbname',
            'foo',
            '--command',
            'ANALYZE',
        ),
        extra_environment={'PGPASSWORD': 'trustsome1'},
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_runs_psql_for_all_database_dump():
    database_config = [{'name': 'all'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('psql', '--no-password'),
        processes=[extract_process],
        input_file=extract_process.stdout,
        extra_environment=None,
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('psql', '--no-password', '--quiet', '--command', 'ANALYZE'), extra_environment=None
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_with_dry_run_skips_restore():
    database_config = [{'name': 'foo'}]

    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=True, extract_process=flexmock()
    )
