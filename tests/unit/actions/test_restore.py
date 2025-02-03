import pytest
from flexmock import flexmock

import borgmatic.actions.restore as module


@pytest.mark.parametrize(
    'first_dump,second_dump,default_port,expected_result',
    (
        (
            module.Dump('postgresql_databases', 'foo'),
            module.Dump('postgresql_databases', 'foo'),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo'),
            module.Dump('postgresql_databases', 'bar'),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', 'foo'),
            module.Dump('mariadb_databases', 'foo'),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', 'foo'),
            module.Dump(module.UNSPECIFIED, 'foo'),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo'),
            module.Dump(module.UNSPECIFIED, 'bar'),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', module.UNSPECIFIED),
            module.Dump('postgresql_databases', 'foo'),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', module.UNSPECIFIED),
            module.Dump('mariadb_databases', 'foo'),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost'),
            module.Dump('postgresql_databases', 'foo', 'myhost'),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost'),
            module.Dump('postgresql_databases', 'foo', 'otherhost'),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost'),
            module.Dump('postgresql_databases', 'foo', module.UNSPECIFIED),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost'),
            module.Dump('postgresql_databases', 'bar', module.UNSPECIFIED),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', 1234),
            module.Dump('postgresql_databases', 'foo', 'myhost', 1234),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', 1234),
            module.Dump('postgresql_databases', 'foo', 'myhost', 4321),
            None,
            False,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', module.UNSPECIFIED),
            module.Dump('postgresql_databases', 'foo', 'myhost', 1234),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', module.UNSPECIFIED),
            module.Dump('postgresql_databases', 'foo', 'otherhost', 1234),
            None,
            False,
        ),
        (
            module.Dump(
                module.UNSPECIFIED, module.UNSPECIFIED, module.UNSPECIFIED, module.UNSPECIFIED
            ),
            module.Dump('postgresql_databases', 'foo', 'myhost', 1234),
            None,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', 5432),
            module.Dump('postgresql_databases', 'foo', 'myhost', None),
            5432,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', None),
            module.Dump('postgresql_databases', 'foo', 'myhost', 5432),
            5432,
            True,
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'myhost', 5433),
            module.Dump('postgresql_databases', 'foo', 'myhost', None),
            5432,
            False,
        ),
    ),
)
def test_dumps_match_compares_two_dumps_while_respecting_unspecified_values(
    first_dump, second_dump, default_port, expected_result
):
    assert module.dumps_match(first_dump, second_dump, default_port) == expected_result


@pytest.mark.parametrize(
    'dump,expected_result',
    (
        (
            module.Dump('postgresql_databases', 'foo'),
            'foo@localhost (postgresql_databases)',
        ),
        (
            module.Dump(module.UNSPECIFIED, 'foo'),
            'foo@localhost',
        ),
        (
            module.Dump('postgresql_databases', module.UNSPECIFIED),
            'unspecified@localhost (postgresql_databases)',
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'host'),
            'foo@host (postgresql_databases)',
        ),
        (
            module.Dump('postgresql_databases', 'foo', module.UNSPECIFIED),
            'foo (postgresql_databases)',
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'host', 1234),
            'foo@host:1234 (postgresql_databases)',
        ),
        (
            module.Dump('postgresql_databases', 'foo', module.UNSPECIFIED, 1234),
            'foo@:1234 (postgresql_databases)',
        ),
        (
            module.Dump('postgresql_databases', 'foo', 'host', module.UNSPECIFIED),
            'foo@host (postgresql_databases)',
        ),
        (
            module.Dump(
                module.UNSPECIFIED, module.UNSPECIFIED, module.UNSPECIFIED, module.UNSPECIFIED
            ),
            'unspecified',
        ),
    ),
)
def test_render_dump_metadata_renders_dump_values_into_string(dump, expected_result):
    assert module.render_dump_metadata(dump) == expected_result


def test_get_configured_data_source_matches_data_source_with_restore_dump():
    default_port = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(default_port)
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump('postgresql_databases', 'bar'),
        module.Dump('postgresql_databases', 'bar'),
        default_port=default_port,
    ).and_return(True)

    assert module.get_configured_data_source(
        config={
            'other_databases': [{'name': 'other'}],
            'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}],
        },
        restore_dump=module.Dump('postgresql_databases', 'bar'),
    ) == {'name': 'bar'}


def test_get_configured_data_source_matches_nothing_when_nothing_configured():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(flexmock())
    flexmock(module).should_receive('dumps_match').and_return(False)

    assert (
        module.get_configured_data_source(
            config={},
            restore_dump=module.Dump('postgresql_databases', 'quux'),
        )
        is None
    )


def test_get_configured_data_source_matches_nothing_when_restore_dump_does_not_match_configuration():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(flexmock())
    flexmock(module).should_receive('dumps_match').and_return(False)

    assert (
        module.get_configured_data_source(
            config={
                'postgresql_databases': [{'name': 'foo'}],
            },
            restore_dump=module.Dump('postgresql_databases', 'quux'),
        )
        is None
    )


def test_get_configured_data_source_with_multiple_matching_data_sources_errors():
    default_port = flexmock()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(default_port)
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump('postgresql_databases', 'bar'),
        module.Dump('postgresql_databases', 'bar'),
        default_port=default_port,
    ).and_return(True)
    flexmock(module).should_receive('render_dump_metadata').and_return('test')

    with pytest.raises(ValueError):
        module.get_configured_data_source(
            config={
                'other_databases': [{'name': 'other'}],
                'postgresql_databases': [
                    {'name': 'foo'},
                    {'name': 'bar'},
                    {'name': 'bar', 'format': 'directory'},
                ],
            },
            restore_dump=module.Dump('postgresql_databases', 'bar'),
        )


def test_strip_path_prefix_from_extracted_dump_destination_renames_first_matching_databases_subdirectory():
    flexmock(module.os).should_receive('walk').and_return(
        [
            ('/foo', flexmock(), flexmock()),
            ('/foo/bar', flexmock(), flexmock()),
            ('/foo/bar/postgresql_databases', flexmock(), flexmock()),
            ('/foo/bar/mariadb_databases', flexmock(), flexmock()),
        ]
    )

    flexmock(module.shutil).should_receive('move').with_args(
        '/foo/bar/postgresql_databases', '/run/user/0/borgmatic/postgresql_databases'
    ).once()
    flexmock(module.shutil).should_receive('move').with_args(
        '/foo/bar/mariadb_databases', '/run/user/0/borgmatic/mariadb_databases'
    ).never()

    module.strip_path_prefix_from_extracted_dump_destination('/foo', '/run/user/0/borgmatic')


def test_restore_single_dump_extracts_and_restores_single_file_dump():
    flexmock(module).should_receive('render_dump_metadata').and_return('test')
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object
    ).and_return({'postgresql': flexmock()})
    flexmock(module.tempfile).should_receive('mkdtemp').never()
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern'
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        flexmock()
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').never()
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        function_name='restore_data_source_dump',
        config=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory=object,
    ).once()

    module.restore_single_dump(
        repository={'path': 'test.borg'},
        config=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
        archive_name=flexmock(),
        hook_name='postgresql',
        data_source={'name': 'test', 'format': 'plain'},
        connection_params=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_single_dump_extracts_and_restores_directory_dump():
    flexmock(module).should_receive('render_dump_metadata').and_return('test')
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object
    ).and_return({'postgresql': flexmock()})
    flexmock(module.tempfile).should_receive('mkdtemp').once().and_return(
        '/run/user/0/borgmatic/tmp1234'
    )
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern'
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        flexmock()
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').once()
    flexmock(module.shutil).should_receive('rmtree').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        function_name='restore_data_source_dump',
        config=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory='/run/borgmatic',
    ).once()

    module.restore_single_dump(
        repository={'path': 'test.borg'},
        config=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(dry_run=False),
        local_path=None,
        remote_path=None,
        archive_name=flexmock(),
        hook_name='postgresql',
        data_source={'name': 'test', 'format': 'directory'},
        connection_params=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_single_dump_with_directory_dump_error_cleans_up_temporary_directory():
    flexmock(module).should_receive('render_dump_metadata').and_return('test')
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object
    ).and_return({'postgresql': flexmock()})
    flexmock(module.tempfile).should_receive('mkdtemp').once().and_return(
        '/run/user/0/borgmatic/tmp1234'
    )
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern'
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_raise(
        ValueError
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').never()
    flexmock(module.shutil).should_receive('rmtree').once()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        function_name='restore_data_source_dump',
        config=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory='/run/user/0/borgmatic/tmp1234',
    ).never()

    with pytest.raises(ValueError):
        module.restore_single_dump(
            repository={'path': 'test.borg'},
            config=flexmock(),
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=False),
            local_path=None,
            remote_path=None,
            archive_name=flexmock(),
            hook_name='postgresql',
            data_source={'name': 'test', 'format': 'directory'},
            connection_params=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_restore_single_dump_with_directory_dump_and_dry_run_skips_directory_move_and_cleanup():
    flexmock(module).should_receive('render_dump_metadata').and_return('test')
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object
    ).and_return({'postgresql': flexmock()})
    flexmock(module.tempfile).should_receive('mkdtemp').once().and_return('/run/borgmatic/tmp1234')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern'
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        flexmock()
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').never()
    flexmock(module.shutil).should_receive('rmtree').never()
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').with_args(
        function_name='restore_data_source_dump',
        config=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory='/run/borgmatic',
    ).once()

    module.restore_single_dump(
        repository={'path': 'test.borg'},
        config=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(dry_run=True),
        local_path=None,
        remote_path=None,
        archive_name=flexmock(),
        hook_name='postgresql',
        data_source={'name': 'test', 'format': 'directory'},
        connection_params=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_collect_dumps_from_archive_parses_archive_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'make_data_source_dump_path'
    ).and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            'borgmatic/postgresql_databases/localhost/foo',
            'borgmatic/postgresql_databases/host:1234/bar',
            'borgmatic/mysql_databases/localhost/quux',
        ]
    )

    archive_dumps = module.collect_dumps_from_archive(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_dumps == {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar', 'host', 1234),
        module.Dump('mysql_databases', 'quux'),
    }


def test_collect_dumps_from_archive_parses_archive_paths_with_different_base_directories():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'make_data_source_dump_path'
    ).and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            'borgmatic/postgresql_databases/localhost/foo',
            '.borgmatic/postgresql_databases/localhost/bar',
            '/root/.borgmatic/postgresql_databases/localhost/baz',
            '/var/run/0/borgmatic/mysql_databases/localhost/quux',
        ]
    )

    archive_dumps = module.collect_dumps_from_archive(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_dumps == {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
        module.Dump('postgresql_databases', 'baz'),
        module.Dump('mysql_databases', 'quux'),
    }


def test_collect_dumps_from_archive_parses_directory_format_archive_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'make_data_source_dump_path'
    ).and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            'borgmatic/postgresql_databases/localhost/foo/table1',
            'borgmatic/postgresql_databases/localhost/foo/table2',
        ]
    )

    archive_dumps = module.collect_dumps_from_archive(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_dumps == {
        module.Dump('postgresql_databases', 'foo'),
    }


def test_collect_dumps_from_archive_skips_bad_archive_paths_or_bad_path_components():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'make_data_source_dump_path'
    ).and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            'borgmatic/postgresql_databases/localhost/foo',
            'borgmatic/postgresql_databases/localhost:abcd/bar',
            'borgmatic/invalid',
            'invalid/as/well',
            '',
        ]
    )

    archive_dumps = module.collect_dumps_from_archive(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_dumps == {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
    }


def test_get_dumps_to_restore_gets_requested_dumps_found_in_archive():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
        module.Dump('postgresql_databases', 'baz'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'bar', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'bar'),
    ).and_return(True)

    assert module.get_dumps_to_restore(
        restore_arguments=flexmock(
            hook=None,
            data_sources=['foo', 'bar'],
            original_hostname=None,
            original_port=None,
        ),
        dumps_from_archive=dumps_from_archive,
    ) == {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
    }


def test_get_dumps_to_restore_raises_for_requested_dumps_missing_from_archive():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('render_dump_metadata').and_return('test')

    with pytest.raises(ValueError):
        module.get_dumps_to_restore(
            restore_arguments=flexmock(
                hook=None,
                data_sources=['foo', 'bar'],
                original_hostname=None,
                original_port=None,
            ),
            dumps_from_archive=dumps_from_archive,
        )


def test_get_dumps_to_restore_without_requested_dumps_finds_all_archive_dumps():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)

    assert (
        module.get_dumps_to_restore(
            restore_arguments=flexmock(
                hook=None,
                data_sources=[],
                original_hostname=None,
                original_port=None,
            ),
            dumps_from_archive=dumps_from_archive,
        )
        == dumps_from_archive
    )


def test_get_dumps_to_restore_with_all_in_requested_dumps_finds_all_archive_dumps():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'bar', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'bar'),
    ).and_return(True)

    assert (
        module.get_dumps_to_restore(
            restore_arguments=flexmock(
                hook=None,
                data_sources=['all'],
                original_hostname=None,
                original_port=None,
            ),
            dumps_from_archive=dumps_from_archive,
        )
        == dumps_from_archive
    )


def test_get_dumps_to_restore_with_all_in_requested_dumps_plus_additional_requested_dumps_omits_duplicates():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'bar', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'bar'),
    ).and_return(True)

    assert (
        module.get_dumps_to_restore(
            restore_arguments=flexmock(
                hook=None,
                data_sources=['all', 'foo', 'bar'],
                original_hostname=None,
                original_port=None,
            ),
            dumps_from_archive=dumps_from_archive,
        )
        == dumps_from_archive
    )


def test_get_dumps_to_restore_raises_for_multiple_matching_dumps_in_archive():
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'foo', hostname=module.UNSPECIFIED),
        module.Dump('mariadb_databases', 'foo'),
    ).and_return(True)
    flexmock(module).should_receive('render_dump_metadata').and_return('test')

    with pytest.raises(ValueError):
        module.get_dumps_to_restore(
            restore_arguments=flexmock(
                hook=None,
                data_sources=['foo'],
                original_hostname=None,
                original_port=None,
            ),
            dumps_from_archive={
                module.Dump('postgresql_databases', 'foo'),
                module.Dump('mariadb_databases', 'foo'),
            },
        )


def test_get_dumps_to_restore_raises_for_all_in_requested_dumps_and_requested_dumps_missing_from_archive():
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump(module.UNSPECIFIED, 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)
    flexmock(module).should_receive('render_dump_metadata').and_return('test')

    with pytest.raises(ValueError):
        module.get_dumps_to_restore(
            restore_arguments=flexmock(
                hook=None,
                data_sources=['all', 'foo', 'bar'],
                original_hostname=None,
                original_port=None,
            ),
            dumps_from_archive={module.Dump('postresql_databases', 'foo')},
        )


def test_get_dumps_to_restore_with_requested_hook_name_filters_dumps_found_in_archive():
    dumps_from_archive = {
        module.Dump('mariadb_databases', 'foo'),
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('sqlite_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump('postgresql_databases', 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)

    assert module.get_dumps_to_restore(
        restore_arguments=flexmock(
            hook='postgresql_databases',
            data_sources=['foo'],
            original_hostname=None,
            original_port=None,
        ),
        dumps_from_archive=dumps_from_archive,
    ) == {
        module.Dump('postgresql_databases', 'foo'),
    }


def test_get_dumps_to_restore_with_requested_shortened_hook_name_filters_dumps_found_in_archive():
    dumps_from_archive = {
        module.Dump('mariadb_databases', 'foo'),
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('sqlite_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump('postgresql_databases', 'foo', hostname=module.UNSPECIFIED),
        module.Dump('postgresql_databases', 'foo'),
    ).and_return(True)

    assert module.get_dumps_to_restore(
        restore_arguments=flexmock(
            hook='postgresql',
            data_sources=['foo'],
            original_hostname=None,
            original_port=None,
        ),
        dumps_from_archive=dumps_from_archive,
    ) == {
        module.Dump('postgresql_databases', 'foo'),
    }


def test_get_dumps_to_restore_with_requested_hostname_filters_dumps_found_in_archive():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo'),
        module.Dump('postgresql_databases', 'foo', 'host'),
        module.Dump('postgresql_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump('postgresql_databases', 'foo', 'host'),
        module.Dump('postgresql_databases', 'foo', 'host'),
    ).and_return(True)

    assert module.get_dumps_to_restore(
        restore_arguments=flexmock(
            hook='postgresql_databases',
            data_sources=['foo'],
            original_hostname='host',
            original_port=None,
        ),
        dumps_from_archive=dumps_from_archive,
    ) == {
        module.Dump('postgresql_databases', 'foo', 'host'),
    }


def test_get_dumps_to_restore_with_requested_port_filters_dumps_found_in_archive():
    dumps_from_archive = {
        module.Dump('postgresql_databases', 'foo', 'host'),
        module.Dump('postgresql_databases', 'foo', 'host', 1234),
        module.Dump('postgresql_databases', 'bar'),
    }
    flexmock(module).should_receive('dumps_match').and_return(False)
    flexmock(module).should_receive('dumps_match').with_args(
        module.Dump('postgresql_databases', 'foo', 'host', 1234),
        module.Dump('postgresql_databases', 'foo', 'host', 1234),
    ).and_return(True)

    assert module.get_dumps_to_restore(
        restore_arguments=flexmock(
            hook='postgresql_databases',
            data_sources=['foo'],
            original_hostname='host',
            original_port=1234,
        ),
        dumps_from_archive=dumps_from_archive,
    ) == {
        module.Dump('postgresql_databases', 'foo', 'host', 1234),
    }


def test_ensure_requested_dumps_restored_with_all_dumps_restored_does_not_raise():
    module.ensure_requested_dumps_restored(
        dumps_to_restore={
            module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
            module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
        },
        dumps_actually_restored={
            module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
            module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
        },
    )


def test_ensure_requested_dumps_restored_with_no_dumps_raises():
    with pytest.raises(ValueError):
        module.ensure_requested_dumps_restored(
            dumps_to_restore={},
            dumps_actually_restored={},
        )


def test_ensure_requested_dumps_restored_with_missing_dumps_raises():
    flexmock(module).should_receive('render_dump_metadata').and_return('test')

    with pytest.raises(ValueError):
        module.ensure_requested_dumps_restored(
            dumps_to_restore={
                module.Dump(hook_name='postgresql_databases', data_source_name='foo')
            },
            dumps_actually_restored={
                module.Dump(hook_name='postgresql_databases', data_source_name='bar')
            },
        )


def test_run_restore_restores_each_data_source():
    dumps_to_restore = {
        module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
        module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    borgmatic_runtime_directory = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        borgmatic_runtime_directory
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob'
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_dumps_from_archive').and_return(flexmock())
    flexmock(module).should_receive('get_dumps_to_restore').and_return(dumps_to_restore)
    flexmock(module).should_receive('get_configured_data_source').and_return(
        {'name': 'foo'}
    ).and_return({'name': 'bar'})
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'foo', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'bar', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('ensure_requested_dumps_restored')

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(
            repository='repo',
            archive='archive',
            data_sources=flexmock(),
            schemas=None,
            hostname=None,
            port=None,
            username=None,
            password=None,
            restore_path=None,
        ),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_bails_for_non_matching_repository():
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(
        False
    )
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob'
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).never()
    flexmock(module).should_receive('restore_single_dump').never()

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', data_sources=flexmock()),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_restores_data_source_by_falling_back_to_all_name():
    dumps_to_restore = {
        module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    borgmatic_runtime_directory = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        borgmatic_runtime_directory
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob'
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_dumps_from_archive').and_return(flexmock())
    flexmock(module).should_receive('get_dumps_to_restore').and_return(dumps_to_restore)
    flexmock(module).should_receive('get_configured_data_source').and_return(
        {'name': 'foo'}
    ).and_return({'name': 'all'})
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'foo', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('ensure_requested_dumps_restored')

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(
            repository='repo',
            archive='archive',
            data_sources=flexmock(),
            schemas=None,
            hostname=None,
            port=None,
            username=None,
            password=None,
            restore_path=None,
        ),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_restores_data_source_configured_with_all_name():
    dumps_to_restore = {
        module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
        module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    borgmatic_runtime_directory = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        borgmatic_runtime_directory
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob'
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_dumps_from_archive').and_return(flexmock())
    flexmock(module).should_receive('get_dumps_to_restore').and_return(dumps_to_restore)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
    ).and_return({'name': 'foo'})
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
    ).and_return(None)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='all'),
    ).and_return({'name': 'bar'})
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'foo', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'bar', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('ensure_requested_dumps_restored')

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(
            repository='repo',
            archive='archive',
            data_sources=flexmock(),
            schemas=None,
            hostname=None,
            port=None,
            username=None,
            password=None,
            restore_path=None,
        ),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_skips_missing_data_source():
    dumps_to_restore = {
        module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
        module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    borgmatic_runtime_directory = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        borgmatic_runtime_directory
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob'
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_dumps_from_archive').and_return(flexmock())
    flexmock(module).should_receive('get_dumps_to_restore').and_return(dumps_to_restore)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
    ).and_return({'name': 'foo'})
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='bar'),
    ).and_return(None)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='all'),
    ).and_return(None)
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'foo', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'bar', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).never()
    flexmock(module).should_receive('ensure_requested_dumps_restored')

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(
            repository='repo',
            archive='archive',
            data_sources=flexmock(),
            schemas=None,
            hostname=None,
            port=None,
            username=None,
            password=None,
            restore_path=None,
        ),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_restores_data_sources_from_different_hooks():
    dumps_to_restore = {
        module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
        module.Dump(hook_name='mysql_databases', data_source_name='foo'),
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    borgmatic_runtime_directory = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        borgmatic_runtime_directory
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'make_runtime_directory_glob'
    ).replace_with(lambda path: path)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_dumps_from_archive').and_return(flexmock())
    flexmock(module).should_receive('get_dumps_to_restore').and_return(dumps_to_restore)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='postgresql_databases', data_source_name='foo'),
    ).and_return({'name': 'foo'})
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        restore_dump=module.Dump(hook_name='mysql_databases', data_source_name='foo'),
    ).and_return({'name': 'bar'})
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        data_source={'name': 'foo', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('restore_single_dump').with_args(
        repository=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='mysql_databases',
        data_source={'name': 'bar', 'schemas': None},
        connection_params=object,
        borgmatic_runtime_directory=borgmatic_runtime_directory,
    ).once()
    flexmock(module).should_receive('ensure_requested_dumps_restored')

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(
            repository='repo',
            archive='archive',
            data_sources=flexmock(),
            schemas=None,
            hostname=None,
            port=None,
            username=None,
            password=None,
            restore_path=None,
        ),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )
