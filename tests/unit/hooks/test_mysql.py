import logging

import pytest
from flexmock import flexmock

from borgmatic.hooks import mysql as module


def test_database_names_to_dump_passes_through_name():
    extra_environment = flexmock()
    log_prefix = ''

    names = module.database_names_to_dump(
        {'name': 'foo'}, extra_environment, log_prefix, dry_run=False
    )

    assert names == ('foo',)


def test_database_names_to_dump_bails_for_dry_run():
    extra_environment = flexmock()
    log_prefix = ''
    flexmock(module).should_receive('execute_command_and_capture_output').never()

    names = module.database_names_to_dump(
        {'name': 'all'}, extra_environment, log_prefix, dry_run=True
    )

    assert names == ()


def test_database_names_to_dump_queries_mysql_for_database_names():
    extra_environment = flexmock()
    log_prefix = ''
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('mysql', '--skip-column-names', '--batch', '--execute', 'show schemas'),
        extra_environment=extra_environment,
    ).and_return('foo\nbar\nmysql\n').once()

    names = module.database_names_to_dump(
        {'name': 'all'}, extra_environment, log_prefix, dry_run=False
    )

    assert names == ('foo', 'bar')


def test_dump_databases_dumps_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_dump_command').with_args(
            database={'name': name},
            log_prefix=object,
            dump_path=object,
            database_names=(name,),
            extra_environment=object,
            dry_run=object,
            dry_run_label=object,
        ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == processes


def test_dump_databases_dumps_with_password():
    database = {'name': 'foo', 'username': 'root', 'password': 'trustsome1'}
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )

    flexmock(module).should_receive('execute_dump_command').with_args(
        database=database,
        log_prefix=object,
        dump_path=object,
        database_names=('foo',),
        extra_environment={'MYSQL_PWD': 'trustsome1'},
        dry_run=object,
        dry_run_label=object,
    ).and_return(process).once()

    assert module.dump_databases([database], 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_dumps_all_databases_at_once():
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo', 'bar'))
    flexmock(module).should_receive('execute_dump_command').with_args(
        database={'name': 'all'},
        log_prefix=object,
        dump_path=object,
        database_names=('foo', 'bar'),
        extra_environment=object,
        dry_run=object,
        dry_run_label=object,
    ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == [process]


def test_dump_databases_dumps_all_databases_separately_when_format_configured():
    databases = [{'name': 'all', 'format': 'sql'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo', 'bar'))

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_dump_command').with_args(
            database={'name': name, 'format': 'sql'},
            log_prefix=object,
            dump_path=object,
            database_names=(name,),
            extra_environment=object,
            dry_run=object,
            dry_run_label=object,
        ).and_return(process).once()

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False) == processes


def test_database_names_to_dump_runs_mysql_with_list_options():
    database = {'name': 'all', 'list_options': '--defaults-extra-file=my.cnf'}
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'mysql',
            '--defaults-extra-file=my.cnf',
            '--skip-column-names',
            '--batch',
            '--execute',
            'show schemas',
        ),
        extra_environment=None,
    ).and_return(('foo\nbar')).once()

    assert module.database_names_to_dump(database, None, 'test.yaml', '') == ('foo', 'bar')


def test_execute_dump_command_runs_mysqldump():
    process = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--add-drop-database', '--databases', 'foo', '>', 'dump',),
        shell=True,
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo'},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mysqldump_without_add_drop_database():
    process = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--databases', 'foo', '>', 'dump',),
        shell=True,
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'add_drop_database': False},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mysqldump_with_hostname_and_port():
    process = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

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
            '>',
            'dump',
        ),
        shell=True,
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'hostname': 'database.example.org', 'port': 5433},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mysqldump_with_username_and_password():
    process = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--add-drop-database', '--user', 'root', '--databases', 'foo', '>', 'dump',),
        shell=True,
        extra_environment={'MYSQL_PWD': 'trustsome1'},
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'username': 'root', 'password': 'trustsome1'},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment={'MYSQL_PWD': 'trustsome1'},
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mysqldump_with_options():
    process = flexmock()
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        ('mysqldump', '--stuff=such', '--add-drop-database', '--databases', 'foo', '>', 'dump',),
        shell=True,
        extra_environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'options': '--stuff=such'},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_with_duplicate_dump_skips_mysqldump():
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert (
        module.execute_dump_command(
            database={'name': 'foo'},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment=None,
            dry_run=True,
            dry_run_label='SO DRY',
        )
        is None
    )


def test_execute_dump_command_with_dry_run_skips_mysqldump():
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').never()

    assert (
        module.execute_dump_command(
            database={'name': 'foo'},
            log_prefix='log',
            dump_path=flexmock(),
            database_names=('foo',),
            extra_environment=None,
            dry_run=True,
            dry_run_label='SO DRY',
        )
        is None
    )


def test_dump_databases_errors_for_missing_all_databases():
    databases = [{'name': 'all'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module).should_receive('database_names_to_dump').and_return(())

    with pytest.raises(ValueError):
        assert module.dump_databases(databases, 'test.yaml', {}, dry_run=False)


def test_dump_databases_does_not_error_for_missing_all_databases_with_dry_run():
    databases = [{'name': 'all'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.dump).should_receive('make_database_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module).should_receive('database_names_to_dump').and_return(())

    assert module.dump_databases(databases, 'test.yaml', {}, dry_run=True) == []


def test_restore_database_dump_runs_mysql_to_restore():
    database_config = [{'name': 'foo'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('mysql', '--batch'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
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


def test_restore_database_dump_runs_mysql_with_options():
    database_config = [{'name': 'foo', 'restore_options': '--harder'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('mysql', '--batch', '--harder'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment=None,
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_runs_mysql_with_hostname_and_port():
    database_config = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'mysql',
            '--batch',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--protocol',
            'tcp',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment=None,
    ).once()

    module.restore_database_dump(
        database_config, 'test.yaml', {}, dry_run=False, extract_process=extract_process
    )


def test_restore_database_dump_runs_mysql_with_username_and_password():
    database_config = [{'name': 'foo', 'username': 'root', 'password': 'trustsome1'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('mysql', '--batch', '--user', 'root'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        extra_environment={'MYSQL_PWD': 'trustsome1'},
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
