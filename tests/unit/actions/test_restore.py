import pytest
from flexmock import flexmock

import borgmatic.actions.restore as module


def test_get_configured_data_source_matches_data_source_by_name():
    assert module.get_configured_data_source(
        config={
            'other_databases': [{'name': 'other'}],
            'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}],
        },
        archive_data_source_names={'postgresql_databases': ['other', 'foo', 'bar']},
        hook_name='postgresql_databases',
        data_source_name='bar',
    ) == ('postgresql_databases', {'name': 'bar'})


def test_get_configured_data_source_matches_nothing_when_nothing_configured():
    assert module.get_configured_data_source(
        config={},
        archive_data_source_names={'postgresql_databases': ['foo']},
        hook_name='postgresql_databases',
        data_source_name='quux',
    ) == (None, None)


def test_get_configured_data_source_matches_nothing_when_data_source_name_not_configured():
    assert module.get_configured_data_source(
        config={'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}]},
        archive_data_source_names={'postgresql_databases': ['foo']},
        hook_name='postgresql_databases',
        data_source_name='quux',
    ) == (None, None)


def test_get_configured_data_source_matches_nothing_when_data_source_name_not_in_archive():
    assert module.get_configured_data_source(
        config={'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}]},
        archive_data_source_names={'postgresql_databases': ['bar']},
        hook_name='postgresql_databases',
        data_source_name='foo',
    ) == (None, None)


def test_get_configured_data_source_matches_data_source_by_configuration_data_source_name():
    assert module.get_configured_data_source(
        config={'postgresql_databases': [{'name': 'all'}, {'name': 'bar'}]},
        archive_data_source_names={'postgresql_databases': ['foo']},
        hook_name='postgresql_databases',
        data_source_name='foo',
        configuration_data_source_name='all',
    ) == ('postgresql_databases', {'name': 'all'})


def test_get_configured_data_source_with_unspecified_hook_matches_data_source_by_name():
    assert module.get_configured_data_source(
        config={
            'other_databases': [{'name': 'other'}],
            'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}],
        },
        archive_data_source_names={'postgresql_databases': ['other', 'foo', 'bar']},
        hook_name=module.UNSPECIFIED_HOOK,
        data_source_name='bar',
    ) == ('postgresql_databases', {'name': 'bar'})


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


def test_restore_single_data_source_extracts_and_restores_single_file_dump():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object, object
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
        log_prefix=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory=object,
    ).once()

    module.restore_single_data_source(
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


def test_restore_single_data_source_extracts_and_restores_directory_dump():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object, object
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
        log_prefix=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory='/run/borgmatic',
    ).once()

    module.restore_single_data_source(
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


def test_restore_single_data_source_with_directory_dump_error_cleans_up_temporary_directory():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object, object
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
        log_prefix=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory='/run/user/0/borgmatic/tmp1234',
    ).never()

    with pytest.raises(ValueError):
        module.restore_single_data_source(
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


def test_restore_single_data_source_with_directory_dump_and_dry_run_skips_directory_move_and_cleanup():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').with_args(
        'make_data_source_dump_patterns', object, object, object, object, object
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
        log_prefix=object,
        hook_name=object,
        data_source=object,
        dry_run=object,
        extract_process=object,
        connection_params=object,
        borgmatic_runtime_directory='/run/borgmatic',
    ).once()

    module.restore_single_data_source(
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


def test_collect_archive_data_source_names_parses_archive_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'make_data_source_dump_path'
    ).and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            'borgmatic/postgresql_databases/localhost/foo',
            'borgmatic/postgresql_databases/localhost/bar',
            'borgmatic/mysql_databases/localhost/quux',
        ]
    )

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_data_source_names == {
        'postgresql_databases': ['foo', 'bar'],
        'mysql_databases': ['quux'],
    }


def test_collect_archive_data_source_names_parses_archive_paths_with_different_base_directories():
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

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_data_source_names == {
        'postgresql_databases': ['foo', 'bar', 'baz'],
        'mysql_databases': ['quux'],
    }


def test_collect_archive_data_source_names_parses_directory_format_archive_paths():
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

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_data_source_names == {
        'postgresql_databases': ['foo'],
    }


def test_collect_archive_data_source_names_skips_bad_archive_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'make_data_source_dump_path'
    ).and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            'borgmatic/postgresql_databases/localhost/foo',
            'borgmatic/invalid',
            'invalid/as/well',
            '',
        ]
    )

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert archive_data_source_names == {
        'postgresql_databases': ['foo'],
    }


def test_find_data_sources_to_restore_passes_through_requested_names_found_in_archive():
    restore_names = module.find_data_sources_to_restore(
        requested_data_source_names=['foo', 'bar'],
        archive_data_source_names={'postresql_databases': ['foo', 'bar', 'baz']},
    )

    assert restore_names == {module.UNSPECIFIED_HOOK: ['foo', 'bar']}


def test_find_data_sources_to_restore_raises_for_requested_names_missing_from_archive():
    with pytest.raises(ValueError):
        module.find_data_sources_to_restore(
            requested_data_source_names=['foo', 'bar'],
            archive_data_source_names={'postresql_databases': ['foo']},
        )


def test_find_data_sources_to_restore_without_requested_names_finds_all_archive_data_sources():
    archive_data_source_names = {'postresql_databases': ['foo', 'bar']}

    restore_names = module.find_data_sources_to_restore(
        requested_data_source_names=[],
        archive_data_source_names=archive_data_source_names,
    )

    assert restore_names == archive_data_source_names


def test_find_data_sources_to_restore_with_all_in_requested_names_finds_all_archive_data_sources():
    archive_data_source_names = {'postresql_databases': ['foo', 'bar']}

    restore_names = module.find_data_sources_to_restore(
        requested_data_source_names=['all'],
        archive_data_source_names=archive_data_source_names,
    )

    assert restore_names == archive_data_source_names


def test_find_data_sources_to_restore_with_all_in_requested_names_plus_additional_requested_names_omits_duplicates():
    archive_data_source_names = {'postresql_databases': ['foo', 'bar']}

    restore_names = module.find_data_sources_to_restore(
        requested_data_source_names=['all', 'foo', 'bar'],
        archive_data_source_names=archive_data_source_names,
    )

    assert restore_names == archive_data_source_names


def test_find_data_sources_to_restore_raises_for_all_in_requested_names_and_requested_named_missing_from_archives():
    with pytest.raises(ValueError):
        module.find_data_sources_to_restore(
            requested_data_source_names=['all', 'foo', 'bar'],
            archive_data_source_names={'postresql_databases': ['foo']},
        )


def test_ensure_data_sources_found_with_all_data_sources_found_does_not_raise():
    module.ensure_data_sources_found(
        restore_names={'postgresql_databases': ['foo']},
        remaining_restore_names={'postgresql_databases': ['bar']},
        found_names=['foo', 'bar'],
    )


def test_ensure_data_sources_found_with_no_data_sources_raises():
    with pytest.raises(ValueError):
        module.ensure_data_sources_found(
            restore_names={'postgresql_databases': []},
            remaining_restore_names={},
            found_names=[],
        )


def test_ensure_data_sources_found_with_missing_data_sources_raises():
    with pytest.raises(ValueError):
        module.ensure_data_sources_found(
            restore_names={'postgresql_databases': ['foo']},
            remaining_restore_names={'postgresql_databases': ['bar']},
            found_names=['foo'],
        )


def test_run_restore_restores_each_data_source():
    restore_names = {
        'postgresql_databases': ['foo', 'bar'],
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
    flexmock(module).should_receive('collect_archive_data_source_names').and_return(flexmock())
    flexmock(module).should_receive('find_data_sources_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_data_source').and_return(
        ('postgresql_databases', {'name': 'foo'})
    ).and_return(('postgresql_databases', {'name': 'bar'}))
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('ensure_data_sources_found')

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
    flexmock(module).should_receive('restore_single_data_source').never()

    module.run_restore(
        repository={'path': 'repo'},
        config=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', data_sources=flexmock()),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_restores_data_source_configured_with_all_name():
    restore_names = {
        'postgresql_databases': ['foo', 'bar'],
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
    flexmock(module).should_receive('collect_archive_data_source_names').and_return(flexmock())
    flexmock(module).should_receive('find_data_sources_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='foo',
    ).and_return(('postgresql_databases', {'name': 'foo'}))
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='bar',
    ).and_return((None, None))
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='bar',
        configuration_data_source_name='all',
    ).and_return(('postgresql_databases', {'name': 'bar'}))
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('ensure_data_sources_found')

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
    restore_names = {
        'postgresql_databases': ['foo', 'bar'],
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
    flexmock(module).should_receive('collect_archive_data_source_names').and_return(flexmock())
    flexmock(module).should_receive('find_data_sources_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='foo',
    ).and_return(('postgresql_databases', {'name': 'foo'}))
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='bar',
    ).and_return((None, None))
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='bar',
        configuration_data_source_name='all',
    ).and_return((None, None))
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('ensure_data_sources_found')

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
    restore_names = {
        'postgresql_databases': ['foo'],
        'mysql_databases': ['bar'],
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
    flexmock(module).should_receive('collect_archive_data_source_names').and_return(flexmock())
    flexmock(module).should_receive('find_data_sources_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='postgresql_databases',
        data_source_name='foo',
    ).and_return(('postgresql_databases', {'name': 'foo'}))
    flexmock(module).should_receive('get_configured_data_source').with_args(
        config=object,
        archive_data_source_names=object,
        hook_name='mysql_databases',
        data_source_name='bar',
    ).and_return(('mysql_databases', {'name': 'bar'}))
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('restore_single_data_source').with_args(
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
    flexmock(module).should_receive('ensure_data_sources_found')

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
