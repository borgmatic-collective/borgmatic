import logging

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import mariadb as module


def test_parse_extra_options_passes_through_empty_options():
    assert module.parse_extra_options('') == ((), None)


def test_parse_extra_options_with_defaults_extra_file_removes_and_and_parses_out_filename():
    assert module.parse_extra_options('--defaults-extra-file=extra.cnf --skip-ssl') == (
        ('--skip-ssl',),
        'extra.cnf',
    )


def test_parse_extra_options_without_defaults_extra_file_passes_through_options():
    assert module.parse_extra_options('--skip-ssl --and=stuff') == (
        ('--skip-ssl', '--and=stuff'),
        None,
    )


def test_make_defaults_file_pipe_without_username_or_password_bails():
    flexmock(module.os).should_receive('pipe').never()

    assert module.make_defaults_file_options(username=None, password=None) == ()


def test_make_defaults_file_option_with_username_and_password_writes_them_to_file_descriptor():
    read_descriptor = 99
    write_descriptor = flexmock()

    flexmock(module.os).should_receive('pipe').and_return(read_descriptor, write_descriptor)
    flexmock(module.os).should_receive('write').with_args(
        write_descriptor, b'[client]\nuser=root\npassword="trustsome1"'
    ).once()
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    assert module.make_defaults_file_options(username='root', password='trustsome1') == (
        '--defaults-extra-file=/dev/fd/99',
    )


def test_make_defaults_file_escapes_password_containing_backslash():
    read_descriptor = 99
    write_descriptor = flexmock()

    flexmock(module.os).should_receive('pipe').and_return(read_descriptor, write_descriptor)
    flexmock(module.os).should_receive('write').with_args(
        write_descriptor, b'[client]\nuser=root\n' + br'password="trust\\nsome1"'
    ).once()
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    assert module.make_defaults_file_options(username='root', password=r'trust\nsome1') == (
        '--defaults-extra-file=/dev/fd/99',
    )


def test_make_defaults_file_pipe_with_only_username_writes_it_to_file_descriptor():
    read_descriptor = 99
    write_descriptor = flexmock()

    flexmock(module.os).should_receive('pipe').and_return(read_descriptor, write_descriptor)
    flexmock(module.os).should_receive('write').with_args(
        write_descriptor, b'[client]\nuser=root'
    ).once()
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    assert module.make_defaults_file_options(username='root', password=None) == (
        '--defaults-extra-file=/dev/fd/99',
    )


def test_make_defaults_file_pipe_with_only_password_writes_it_to_file_descriptor():
    read_descriptor = 99
    write_descriptor = flexmock()

    flexmock(module.os).should_receive('pipe').and_return(read_descriptor, write_descriptor)
    flexmock(module.os).should_receive('write').with_args(
        write_descriptor, b'[client]\npassword="trustsome1"'
    ).once()
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    assert module.make_defaults_file_options(username=None, password='trustsome1') == (
        '--defaults-extra-file=/dev/fd/99',
    )


def test_make_defaults_file_option_with_defaults_extra_filename_includes_it_in_file_descriptor():
    read_descriptor = 99
    write_descriptor = flexmock()

    flexmock(module.os).should_receive('pipe').and_return(read_descriptor, write_descriptor)
    flexmock(module.os).should_receive('write').with_args(
        write_descriptor, b'!include extra.cnf\n[client]\nuser=root\npassword="trustsome1"'
    ).once()
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    assert module.make_defaults_file_options(
        username='root', password='trustsome1', defaults_extra_filename='extra.cnf'
    ) == ('--defaults-extra-file=/dev/fd/99',)


def test_make_defaults_file_option_with_only_defaults_extra_filename_uses_it_instead_of_file_descriptor():
    flexmock(module.os).should_receive('pipe').never()

    assert module.make_defaults_file_options(
        username=None, password=None, defaults_extra_filename='extra.cnf'
    ) == ('--defaults-extra-file=extra.cnf',)


def test_database_names_to_dump_passes_through_name():
    environment = flexmock()

    names = module.database_names_to_dump(
        {'name': 'foo'}, {}, 'root', 'trustsome1', environment, dry_run=False
    )

    assert names == ('foo',)


def test_database_names_to_dump_bails_for_dry_run():
    environment = flexmock()
    flexmock(module).should_receive('execute_command_and_capture_output').never()

    names = module.database_names_to_dump(
        {'name': 'all'}, {}, 'root', 'trustsome1', environment, dry_run=True
    )

    assert names == ()


def test_database_names_to_dump_queries_mariadb_for_database_names():
    environment = flexmock()
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'mariadb',
            '--defaults-extra-file=/dev/fd/99',
            '--skip-column-names',
            '--batch',
            '--execute',
            'show schemas',
        ),
        environment=environment,
    ).and_return('foo\nbar\nmysql\n').once()

    names = module.database_names_to_dump(
        {'name': 'all'}, {}, 'root', 'trustsome1', environment, dry_run=False
    )

    assert names == ('foo', 'bar')


def test_database_names_to_dump_runs_mariadb_with_tls():
    environment = flexmock()
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'mariadb',
            '--defaults-extra-file=/dev/fd/99',
            '--ssl',
            '--skip-column-names',
            '--batch',
            '--execute',
            'show schemas',
        ),
        environment=environment,
    ).and_return('foo\nbar\nmysql\n').once()

    names = module.database_names_to_dump(
        {'name': 'all', 'tls': True}, {}, 'root', 'trustsome1', environment, dry_run=False
    )

    assert names == ('foo', 'bar')


def test_database_names_to_dump_runs_mariadb_without_tls():
    environment = flexmock()
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'mariadb',
            '--defaults-extra-file=/dev/fd/99',
            '--skip-ssl',
            '--skip-column-names',
            '--batch',
            '--execute',
            'show schemas',
        ),
        environment=environment,
    ).and_return('foo\nbar\nmysql\n').once()

    names = module.database_names_to_dump(
        {'name': 'all', 'tls': False}, {}, 'root', 'trustsome1', environment, dry_run=False
    )

    assert names == ('foo', 'bar')


def test_use_streaming_true_for_any_databases():
    assert module.use_streaming(
        databases=[flexmock(), flexmock()],
        config=flexmock(),
    )


def test_use_streaming_false_for_no_databases():
    assert not module.use_streaming(databases=[], config=flexmock())


def test_dump_data_sources_dumps_each_database():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock()
    )
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_dump_command').with_args(
            database={'name': name},
            config={},
            username=None,
            password=None,
            dump_path=object,
            database_names=(name,),
            environment={'USER': 'root'},
            dry_run=object,
            dry_run_label=object,
        ).and_return(process).once()

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


def test_dump_data_sources_dumps_with_password():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock()
    )
    database = {'name': 'foo', 'username': 'root', 'password': 'trustsome1'}
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo',)).and_return(
        ('bar',)
    )

    flexmock(module).should_receive('execute_dump_command').with_args(
        database=database,
        config={},
        username='root',
        password='trustsome1',
        dump_path=object,
        database_names=('foo',),
        environment={'USER': 'root'},
        dry_run=object,
        dry_run_label=object,
    ).and_return(process).once()

    assert module.dump_data_sources(
        [database],
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_dumps_all_databases_at_once():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock()
    )
    databases = [{'name': 'all'}]
    process = flexmock()
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo', 'bar'))
    flexmock(module).should_receive('execute_dump_command').with_args(
        database={'name': 'all'},
        config={},
        username=None,
        password=None,
        dump_path=object,
        database_names=('foo', 'bar'),
        environment={'USER': 'root'},
        dry_run=object,
        dry_run_label=object,
    ).and_return(process).once()

    assert module.dump_data_sources(
        databases,
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    ) == [process]


def test_dump_data_sources_dumps_all_databases_separately_when_format_configured():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock()
    )
    databases = [{'name': 'all', 'format': 'sql'}]
    processes = [flexmock(), flexmock()]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('database_names_to_dump').and_return(('foo', 'bar'))

    for name, process in zip(('foo', 'bar'), processes):
        flexmock(module).should_receive('execute_dump_command').with_args(
            database={'name': name, 'format': 'sql'},
            config={},
            username=None,
            password=None,
            dump_path=object,
            database_names=(name,),
            environment={'USER': 'root'},
            dry_run=object,
            dry_run_label=object,
        ).and_return(process).once()

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


def test_database_names_to_dump_runs_mariadb_with_list_options():
    database = {'name': 'all', 'list_options': '--defaults-extra-file=mariadb.cnf --skip-ssl'}
    flexmock(module).should_receive('parse_extra_options').and_return(
        ('--skip-ssl',), 'mariadb.cnf'
    )
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', 'mariadb.cnf'
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        (
            'mariadb',
            '--defaults-extra-file=/dev/fd/99',
            '--skip-ssl',
            '--skip-column-names',
            '--batch',
            '--execute',
            'show schemas',
        ),
        environment=None,
    ).and_return(('foo\nbar')).once()

    assert module.database_names_to_dump(database, {}, 'root', 'trustsome1', None, '') == (
        'foo',
        'bar',
    )


def test_database_names_to_dump_runs_non_default_mariadb_with_list_options():
    database = {
        'name': 'all',
        'list_options': '--defaults-extra-file=mariadb.cnf --skip-ssl',
        'mariadb_command': 'custom_mariadb',
    }
    flexmock(module).should_receive('parse_extra_options').and_return(
        ('--skip-ssl',), 'mariadb.cnf'
    )
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', 'mariadb.cnf'
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        environment=None,
        full_command=(
            'custom_mariadb',  # Custom MariaDB command
            '--defaults-extra-file=/dev/fd/99',
            '--skip-ssl',
            '--skip-column-names',
            '--batch',
            '--execute',
            'show schemas',
        ),
    ).and_return(('foo\nbar')).once()

    assert module.database_names_to_dump(database, {}, 'root', 'trustsome1', None, '') == (
        'foo',
        'bar',
    )


def test_execute_dump_command_runs_mariadb_dump():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--add-drop-database',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo'},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mariadb_dump_without_add_drop_database():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'add_drop_database': False},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mariadb_dump_with_hostname_and_port():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--add-drop-database',
            '--host',
            'database.example.org',
            '--port',
            '5433',
            '--protocol',
            'tcp',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'hostname': 'database.example.org', 'port': 5433},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mariadb_dump_with_tls():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--add-drop-database',
            '--ssl',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'tls': True},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mariadb_dump_without_tls():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--add-drop-database',
            '--skip-ssl',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'tls': False},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mariadb_dump_with_username_and_password():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--add-drop-database',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment={},
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'username': 'root', 'password': 'trustsome1'},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment={},
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_mariadb_dump_with_options():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return(('--stuff=such',), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'mariadb-dump',
            '--defaults-extra-file=/dev/fd/99',
            '--stuff=such',
            '--add-drop-database',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={'name': 'foo', 'options': '--stuff=such'},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_runs_non_default_mariadb_dump_with_options():
    process = flexmock()
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return(('--stuff=such',), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').with_args(
        (
            'custom_mariadb_dump',  # Custom MariaDB dump command
            '--defaults-extra-file=/dev/fd/99',
            '--stuff=such',
            '--add-drop-database',
            '--databases',
            'foo',
            '--result-file',
            'dump',
        ),
        environment=None,
        run_to_completion=False,
    ).and_return(process).once()

    assert (
        module.execute_dump_command(
            database={
                'name': 'foo',
                'mariadb_dump_command': 'custom_mariadb_dump',
                'options': '--stuff=such',
            },  # Custom MariaDB dump command specified
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=False,
            dry_run_label='',
        )
        == process
    )


def test_execute_dump_command_with_duplicate_dump_skips_mariadb_dump():
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()

    assert (
        module.execute_dump_command(
            database={'name': 'foo'},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=True,
            dry_run_label='SO DRY',
        )
        is None
    )


def test_execute_dump_command_with_dry_run_skips_mariadb_dump():
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return('dump')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')

    flexmock(module).should_receive('execute_command').never()

    assert (
        module.execute_dump_command(
            database={'name': 'foo'},
            config={},
            username='root',
            password='trustsome1',
            dump_path=flexmock(),
            database_names=('foo',),
            environment=None,
            dry_run=True,
            dry_run_label='SO DRY',
        )
        is None
    )


def test_dump_data_sources_errors_for_missing_all_databases():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock()
    )
    databases = [{'name': 'all'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module).should_receive('database_names_to_dump').and_return(())

    with pytest.raises(ValueError):
        assert module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=False,
        )


def test_dump_data_sources_does_not_error_for_missing_all_databases_with_dry_run():
    flexmock(module.borgmatic.hooks.command).should_receive('Before_after_hooks').and_return(
        flexmock()
    )
    databases = [{'name': 'all'}]
    flexmock(module).should_receive('make_dump_path').and_return('')
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        'databases/localhost/all'
    )
    flexmock(module).should_receive('database_names_to_dump').and_return(())

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


def test_restore_data_source_dump_runs_mariadb_to_restore():
    hook_config = [{'name': 'foo'}, {'name': 'bar'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('mariadb', '--batch'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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


def test_restore_data_source_dump_runs_mariadb_with_options():
    hook_config = [{'name': 'foo', 'restore_options': '--harder'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return(('--harder',), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('mariadb', '--harder', '--batch'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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


def test_restore_data_source_dump_runs_non_default_mariadb_with_options():
    hook_config = [
        {'name': 'foo', 'restore_options': '--harder', 'mariadb_command': 'custom_mariadb'}
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return(('--harder',), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('custom_mariadb', '--harder', '--batch'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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


def test_restore_data_source_dump_runs_mariadb_with_hostname_and_port():
    hook_config = [{'name': 'foo', 'hostname': 'database.example.org', 'port': 5433}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'mariadb',
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
        environment={'USER': 'root'},
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


def test_restore_data_source_dump_runs_mariadb_with_tls():
    hook_config = [{'name': 'foo', 'tls': True}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'mariadb',
            '--batch',
            '--ssl',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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


def test_restore_data_source_dump_runs_mariadb_without_tls():
    hook_config = [{'name': 'foo', 'tls': False}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'mariadb',
            '--batch',
            '--skip-ssl',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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


def test_restore_data_source_dump_runs_mariadb_with_username_and_password():
    hook_config = [{'name': 'foo', 'username': 'root', 'password': 'trustsome1'}]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'root', 'trustsome1', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('mariadb', '--defaults-extra-file=/dev/fd/99', '--batch'),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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
            'username': 'root',
            'password': 'trustsome1',
            'restore_hostname': 'restorehost',
            'restore_port': 'restoreport',
            'restore_username': 'restoreusername',
            'restore_password': 'restorepassword',
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'cliusername', 'clipassword', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'mariadb',
            '--defaults-extra-file=/dev/fd/99',
            '--batch',
            '--host',
            'clihost',
            '--port',
            'cliport',
            '--protocol',
            'tcp',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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
            'username': 'root',
            'password': 'trustsome1',
            'hostname': 'dbhost',
            'port': 'dbport',
            'tls': True,
            'restore_username': 'restoreuser',
            'restore_password': 'restorepass',
            'restore_hostname': 'restorehost',
            'restore_port': 'restoreport',
            'restore_tls': False,
        }
    ]
    extract_process = flexmock(stdout=flexmock())

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        'restoreuser', 'restorepass', None
    ).and_return(('--defaults-extra-file=/dev/fd/99',))
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        (
            'mariadb',
            '--defaults-extra-file=/dev/fd/99',
            '--batch',
            '--host',
            'restorehost',
            '--port',
            'restoreport',
            '--protocol',
            'tcp',
            '--skip-ssl',
        ),
        processes=[extract_process],
        output_log_level=logging.DEBUG,
        input_file=extract_process.stdout,
        environment={'USER': 'root'},
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
    hook_config = [{'name': 'foo'}]

    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module).should_receive('parse_extra_options').and_return((), None)
    flexmock(module).should_receive('make_defaults_file_options').with_args(
        None, None, None
    ).and_return(())
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
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
