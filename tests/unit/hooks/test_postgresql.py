import logging

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
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})

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
                'databases/localhost/{}'.format(name),
            ),
            shell=True,
            extra_environment={'PGSSLMODE': 'disable'},
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
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
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
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})

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

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_runs_pg_dump_with_username_and_password():
    databases = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'}
    )

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

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


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


def test_dump_databases_runs_pg_dump_with_directory_format():
    databases = [{'name': 'foo', 'format': 'directory'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.dump).should_receive('create_parent_directory_for_dump')
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})

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
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})

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

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_runs_pg_dumpall_for_all_databases():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})

    flexmock(module).should_receive('execute_command').with_args(
        ('pg_dumpall', '--no-password', '--clean', '--if-exists', '>', 'databases/localhost/all'),
        shell=True,
        extra_environment={'PGSSLMODE': 'disable'},
        run_to_completion=False,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_restore_database_dump_runs_pg_restore():
    database_config = [{'name': 'foo'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
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
        ('psql', '--no-password', '--quiet', '--dbname', 'foo', '--command', 'ANALYZE'),
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_errors_on_multiple_database_config():
    database_config = [{'name': 'foo'}, {'name': 'bar'}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('execute_command_with_processes').never()
    flexmock(module).should_receive('execute_command').never()

    with pytest.raises(ValueError):
        module.restore_database_dump(
            database_config, 'test.yaml', {}, dry_run=False, extract_process=flexmock()
        )


def test_restore_database_dump_runs_pg_restore_with_hostname_and_port():
    database_config = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
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

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_runs_pg_restore_with_username_and_password():
    database_config = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename')
    flexmock(module).should_receive('make_extra_environment').and_return(
        {'PGPASSWORD': 'trustsome1', 'PGSSLMODE': 'disable'}
    )
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

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_runs_psql_for_all_database_dump():
    database_config = [{'name': 'all'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('psql', '--no-password'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('psql', '--no-password', '--quiet', '--command', 'ANALYZE'),
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_with_dry_run_skips_restore():
    database_config = [{'name': 'foo'}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=True, extract_process=flexmock()
    )


def test_restore_database_dump_without_extract_process_restores_from_disk():
    database_config = [{'name': 'foo'}]

    flexmock(module).should_receive('make_dump_path')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('/dump/path')
    flexmock(module).should_receive('make_extra_environment').and_return({'PGSSLMODE': 'disable'})
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
        ('psql', '--no-password', '--quiet', '--dbname', 'foo', '--command', 'ANALYZE'),
        extra_environment={'PGSSLMODE': 'disable'},
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=None
    )
