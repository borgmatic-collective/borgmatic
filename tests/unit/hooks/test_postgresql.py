import pytest
from flexmock import flexmock

from borgmatic.hooks import postgresql as module


def test_dump_databases_runs_pg_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
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
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
    flexmock(module.os).should_receive('makedirs')
    flexmock(module).should_receive('execute_command').never()

    module.dump_databases(databases, 'test.yaml', dry_run=True)


def test_dump_databases_without_databases_does_not_raise():
    module.dump_databases([], 'test.yaml', dry_run=False)


def test_dump_databases_with_invalid_database_name_raises():
    databases = [{'name': 'heehee/../../etc/passwd'}]

    with pytest.raises(ValueError):
        module.dump_databases(databases, 'test.yaml', dry_run=True)


def test_dump_databases_runs_pg_dump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
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
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
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
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
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
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
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
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')
    flexmock(module.os).should_receive('makedirs')

    flexmock(module).should_receive('execute_command').with_args(
        ('pg_dumpall', '--no-password', '--clean', '--file', 'databases/localhost/all'),
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)
