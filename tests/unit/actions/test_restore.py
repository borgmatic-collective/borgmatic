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


def test_collect_archive_data_source_names_parses_archive_paths():
    flexmock(module.borgmatic.hooks.dump).should_receive('make_data_source_dump_path').and_return(
        ''
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            '.borgmatic/postgresql_databases/localhost/foo',
            '.borgmatic/postgresql_databases/localhost/bar',
            '.borgmatic/mysql_databases/localhost/quux',
        ]
    )

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={'borgmatic_source_directory': '.borgmatic'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )

    assert archive_data_source_names == {
        'postgresql_databases': ['foo', 'bar'],
        'mysql_databases': ['quux'],
    }


def test_collect_archive_data_source_names_parses_directory_format_archive_paths():
    flexmock(module.borgmatic.hooks.dump).should_receive('make_data_source_dump_path').and_return(
        ''
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            '.borgmatic/postgresql_databases/localhost/foo/table1',
            '.borgmatic/postgresql_databases/localhost/foo/table2',
        ]
    )

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={'borgmatic_source_directory': '.borgmatic'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )

    assert archive_data_source_names == {
        'postgresql_databases': ['foo'],
    }


def test_collect_archive_data_source_names_skips_bad_archive_paths():
    flexmock(module.borgmatic.hooks.dump).should_receive('make_data_source_dump_path').and_return(
        ''
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['.borgmatic/postgresql_databases/localhost/foo', '.borgmatic/invalid', 'invalid/as/well']
    )

    archive_data_source_names = module.collect_archive_data_source_names(
        repository={'path': 'repo'},
        archive='archive',
        config={'borgmatic_source_directory': '.borgmatic'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
        local_path=flexmock(),
        remote_path=flexmock(),
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
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
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
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
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
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
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
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
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
