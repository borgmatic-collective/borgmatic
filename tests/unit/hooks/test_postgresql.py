from flexmock import flexmock

from borgmatic.hooks import postgresql as module


def test_dump_databases_runs_pg_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os).should_receive('makedirs')

    for name in ('foo', 'bar'):
        flexmock(module).should_receive('execute_command').with_args(
            (
                'pg_dump',
                '--no-password',
                '--clean',
                '--file',
                'databases/localhost/{}'.format(name),
                '--format',
                'custom',
                name,
            ),
            extra_environment=None,
        ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_with_dry_run_skips_pg_dump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module).should_receive('execute_command').never()

    module.dump_databases(databases, 'test.yaml', dry_run=True)


def test_dump_databases_runs_pg_dump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/database.example.org/foo'
    )
    flexmock(module.os).should_receive('makedirs')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
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
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_pg_dump_with_username_and_password():
    databases = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os).should_receive('makedirs')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--file',
            'databases/localhost/foo',
            '--username',
            'postgres',
            '--format',
            'custom',
            'foo',
        ),
        extra_environment={'PGPASSWORD': 'trustsome1'},
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_pg_dump_with_format():
    databases = [{'name': 'foo', 'format': 'tar'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os).should_receive('makedirs')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--file',
            'databases/localhost/foo',
            '--format',
            'tar',
            'foo',
        ),
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_pg_dump_with_options():
    databases = [{'name': 'foo', 'options': '--stuff=such'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os).should_receive('makedirs')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_dump',
            '--no-password',
            '--clean',
            '--file',
            'databases/localhost/foo',
            '--format',
            'custom',
            '--stuff=such',
            'foo',
        ),
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_pg_dumpall_for_all_databases():
    databases = [{'name': 'all'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module.os).should_receive('makedirs')

    flexmock(module).should_receive('execute_command').with_args(
        ('pg_dumpall', '--no-password', '--clean', '--file', 'databases/localhost/all'),
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_make_database_dump_patterns_converts_names_to_glob_paths():
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/*/foo'
    ).and_return('databases/*/bar')

    assert module.make_database_dump_patterns(flexmock(), flexmock(), ('foo', 'bar')) == [
        'databases/*/foo',
        'databases/*/bar',
    ]


def test_make_database_dump_patterns_treats_empty_names_as_matching_all_databases():
    flexmock(module.dump).should_receive('make_database_dump_filename').with_args(
        module.DUMP_PATH, '*', '*'
    ).and_return('databases/*/*')

    assert module.make_database_dump_patterns(flexmock(), flexmock(), ()) == ['databases/*/*']


def test_restore_database_dumps_restores_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')

    for name in ('foo', 'bar'):
        flexmock(module).should_receive('execute_command').with_args(
            (
                'pg_restore',
                '--no-password',
                '--clean',
                '--if-exists',
                '--exit-on-error',
                '--dbname',
                name,
                'databases/localhost/{}'.format(name),
            ),
            extra_environment=None,
        ).once()
        flexmock(module).should_receive('execute_command').with_args(
            ('psql', '--no-password', '--quiet', '--dbname', name, '--command', 'ANALYZE'),
            extra_environment=None,
        ).once()

    module.restore_database_dumps(databases, 'test.yaml', dry_run=False)


def test_restore_database_dumps_runs_pg_restore_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_restore',
            '--no-password',
            '--clean',
            '--if-exists',
            '--exit-on-error',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--dbname',
            'foo',
            'databases/localhost/foo',
        ),
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

    module.restore_database_dumps(databases, 'test.yaml', dry_run=False)


def test_restore_database_dumps_runs_pg_restore_with_username_and_password():
    databases = [{'name': 'foo', 'username': 'postgres', 'password': 'trustsome1'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'pg_restore',
            '--no-password',
            '--clean',
            '--if-exists',
            '--exit-on-error',
            '--username',
            'postgres',
            '--dbname',
            'foo',
            'databases/localhost/foo',
        ),
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

    module.restore_database_dumps(databases, 'test.yaml', dry_run=False)
