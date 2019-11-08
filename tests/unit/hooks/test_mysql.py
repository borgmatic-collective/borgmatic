import sys

from flexmock import flexmock

from borgmatic.hooks import mysql as module


def test_dump_databases_runs_mysqldump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    output_file = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os).should_receive('makedirs')
    flexmock(sys.modules['builtins']).should_receive('open').and_return(output_file)

    for name in ('foo', 'bar'):
        flexmock(module).should_receive('execute_command').with_args(
            ('mysqldump', '--add-drop-database', '--databases', name),
            output_file=output_file,
            extra_environment=None,
        ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_with_dry_run_skips_mysqldump():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    ).and_return('databases/localhost/bar')
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module).should_receive('execute_command').never()

    module.dump_databases(databases, 'test.yaml', dry_run=True)


def test_dump_databases_without_databases_does_not_raise():
    module.dump_databases([], 'test.yaml', dry_run=False)


def test_dump_databases_runs_mysqldump_with_hostname_and_port():
    databases = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    output_file = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/database.example.org/foo'
    )
    flexmock(module.os).should_receive('makedirs')
    flexmock(sys.modules['builtins']).should_receive('open').and_return(output_file)

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mysqldump',
            '--add-drop-database',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--protocol',
            'tcp',
            '--databases',
            'foo',
        ),
        output_file=output_file,
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_mysqldump_with_username_and_password():
    databases = [{'name': 'foo', 'username': 'root', 'password': 'trustsome1'}]
    output_file = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os).should_receive('makedirs')
    flexmock(sys.modules['builtins']).should_receive('open').and_return(output_file)

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--add-drop-database', '--user', 'root', '--databases', 'foo'),
        output_file=output_file,
        extra_environment={'MYSQL_PWD': 'trustsome1'},
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_mysqldump_with_options():
    databases = [{'name': 'foo', 'options': '--stuff=such'}]
    output_file = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/foo'
    )
    flexmock(module.os).should_receive('makedirs')
    flexmock(sys.modules['builtins']).should_receive('open').and_return(output_file)

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--add-drop-database', '--stuff=such', '--databases', 'foo'),
        output_file=output_file,
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)


def test_dump_databases_runs_mysqldump_for_all_databases():
    databases = [{'name': 'all'}]
    output_file = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module.os).should_receive('makedirs')
    flexmock(sys.modules['builtins']).should_receive('open').and_return(output_file)

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--add-drop-database', '--all-databases'),
        output_file=output_file,
        extra_environment=None,
    ).once()

    module.dump_databases(databases, 'test.yaml', dry_run=False)
