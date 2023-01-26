import pytest
from flexmock import flexmock

import borgmatic.actions.restore as module


def test_get_configured_database_matches_database_by_name():
    assert module.get_configured_database(
        hooks={
            'other_databases': [{'name': 'other'}],
            'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}],
        },
        archive_database_names={'postgresql_databases': ['other', 'foo', 'bar']},
        hook_name='postgresql_databases',
        database_name='bar',
    ) == ('postgresql_databases', {'name': 'bar'})


def test_get_configured_database_matches_nothing_when_database_name_not_configured():
    assert module.get_configured_database(
        hooks={'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}]},
        archive_database_names={'postgresql_databases': ['foo']},
        hook_name='postgresql_databases',
        database_name='quux',
    ) == (None, None)


def test_get_configured_database_matches_nothing_when_database_name_not_in_archive():
    assert module.get_configured_database(
        hooks={'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}]},
        archive_database_names={'postgresql_databases': ['bar']},
        hook_name='postgresql_databases',
        database_name='foo',
    ) == (None, None)


def test_get_configured_database_matches_database_by_configuration_database_name():
    assert module.get_configured_database(
        hooks={'postgresql_databases': [{'name': 'all'}, {'name': 'bar'}]},
        archive_database_names={'postgresql_databases': ['foo']},
        hook_name='postgresql_databases',
        database_name='foo',
        configuration_database_name='all',
    ) == ('postgresql_databases', {'name': 'all'})


def test_get_configured_database_with_unspecified_hook_matches_database_by_name():
    assert module.get_configured_database(
        hooks={
            'other_databases': [{'name': 'other'}],
            'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}],
        },
        archive_database_names={'postgresql_databases': ['other', 'foo', 'bar']},
        hook_name=module.UNSPECIFIED_HOOK,
        database_name='bar',
    ) == ('postgresql_databases', {'name': 'bar'})


def test_collect_archive_database_names_parses_archive_paths():
    flexmock(module.borgmatic.hooks.dump).should_receive('make_database_dump_path').and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            '.borgmatic/postgresql_databases/localhost/foo',
            '.borgmatic/postgresql_databases/localhost/bar',
            '.borgmatic/mysql_databases/localhost/quux',
        ]
    )

    archive_database_names = module.collect_archive_database_names(
        repository='repo',
        archive='archive',
        location={'borgmatic_source_directory': '.borgmatic'},
        storage=flexmock(),
        local_borg_version=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
    )

    assert archive_database_names == {
        'postgresql_databases': ['foo', 'bar'],
        'mysql_databases': ['quux'],
    }


def test_collect_archive_database_names_parses_directory_format_archive_paths():
    flexmock(module.borgmatic.hooks.dump).should_receive('make_database_dump_path').and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        [
            '.borgmatic/postgresql_databases/localhost/foo/table1',
            '.borgmatic/postgresql_databases/localhost/foo/table2',
        ]
    )

    archive_database_names = module.collect_archive_database_names(
        repository='repo',
        archive='archive',
        location={'borgmatic_source_directory': '.borgmatic'},
        storage=flexmock(),
        local_borg_version=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
    )

    assert archive_database_names == {
        'postgresql_databases': ['foo'],
    }


def test_collect_archive_database_names_skips_bad_archive_paths():
    flexmock(module.borgmatic.hooks.dump).should_receive('make_database_dump_path').and_return('')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['.borgmatic/postgresql_databases/localhost/foo', '.borgmatic/invalid', 'invalid/as/well']
    )

    archive_database_names = module.collect_archive_database_names(
        repository='repo',
        archive='archive',
        location={'borgmatic_source_directory': '.borgmatic'},
        storage=flexmock(),
        local_borg_version=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
    )

    assert archive_database_names == {
        'postgresql_databases': ['foo'],
    }


def test_find_databases_to_restore_passes_through_requested_names_found_in_archive():
    restore_names = module.find_databases_to_restore(
        requested_database_names=['foo', 'bar'],
        archive_database_names={'postresql_databases': ['foo', 'bar', 'baz']},
    )

    assert restore_names == {module.UNSPECIFIED_HOOK: ['foo', 'bar']}


def test_find_databases_to_restore_raises_for_requested_names_missing_from_archive():
    with pytest.raises(ValueError):
        module.find_databases_to_restore(
            requested_database_names=['foo', 'bar'],
            archive_database_names={'postresql_databases': ['foo']},
        )


def test_find_databases_to_restore_without_requested_names_finds_all_archive_databases():
    archive_database_names = {'postresql_databases': ['foo', 'bar']}

    restore_names = module.find_databases_to_restore(
        requested_database_names=[], archive_database_names=archive_database_names,
    )

    assert restore_names == archive_database_names


def test_find_databases_to_restore_with_all_in_requested_names_finds_all_archive_databases():
    archive_database_names = {'postresql_databases': ['foo', 'bar']}

    restore_names = module.find_databases_to_restore(
        requested_database_names=['all'], archive_database_names=archive_database_names,
    )

    assert restore_names == archive_database_names


def test_find_databases_to_restore_with_all_in_requested_names_plus_additional_requested_names_omits_duplicates():
    archive_database_names = {'postresql_databases': ['foo', 'bar']}

    restore_names = module.find_databases_to_restore(
        requested_database_names=['all', 'foo', 'bar'],
        archive_database_names=archive_database_names,
    )

    assert restore_names == archive_database_names


def test_find_databases_to_restore_raises_for_all_in_requested_names_and_requested_named_missing_from_archives():
    with pytest.raises(ValueError):
        module.find_databases_to_restore(
            requested_database_names=['all', 'foo', 'bar'],
            archive_database_names={'postresql_databases': ['foo']},
        )


def test_ensure_databases_found_with_all_databases_found_does_not_raise():
    module.ensure_databases_found(
        restore_names={'postgresql_databases': ['foo']},
        remaining_restore_names={'postgresql_databases': ['bar']},
        found_names=['foo', 'bar'],
    )


def test_ensure_databases_found_with_no_databases_raises():
    with pytest.raises(ValueError):
        module.ensure_databases_found(
            restore_names={'postgresql_databases': []}, remaining_restore_names={}, found_names=[],
        )


def test_ensure_databases_found_with_missing_databases_raises():
    with pytest.raises(ValueError):
        module.ensure_databases_found(
            restore_names={'postgresql_databases': ['foo']},
            remaining_restore_names={'postgresql_databases': ['bar']},
            found_names=['foo'],
        )


def test_run_restore_restores_each_database():
    restore_names = {
        'postgresql_databases': ['foo', 'bar'],
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_archive_database_names').and_return(flexmock())
    flexmock(module).should_receive('find_databases_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_database').and_return(
        ('postgresql_databases', {'name': 'foo'})
    ).and_return(('postgresql_databases', {'name': 'bar'}))
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'foo'},
    ).once()
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'bar'},
    ).once()
    flexmock(module).should_receive('ensure_databases_found')

    module.run_restore(
        repository='repo',
        location=flexmock(),
        storage=flexmock(),
        hooks=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', databases=flexmock()),
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
    flexmock(module).should_receive('restore_single_database').never()

    module.run_restore(
        repository='repo',
        location=flexmock(),
        storage=flexmock(),
        hooks=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', databases=flexmock()),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_restores_database_configured_with_all_name():
    restore_names = {
        'postgresql_databases': ['foo', 'bar'],
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_archive_database_names').and_return(flexmock())
    flexmock(module).should_receive('find_databases_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='foo',
    ).and_return(('postgresql_databases', {'name': 'foo'}))
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='bar',
    ).and_return((None, None))
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='bar',
        configuration_database_name='all',
    ).and_return(('postgresql_databases', {'name': 'bar'}))
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'foo'},
    ).once()
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'bar'},
    ).once()
    flexmock(module).should_receive('ensure_databases_found')

    module.run_restore(
        repository='repo',
        location=flexmock(),
        storage=flexmock(),
        hooks=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', databases=flexmock()),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_skips_missing_database():
    restore_names = {
        'postgresql_databases': ['foo', 'bar'],
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_archive_database_names').and_return(flexmock())
    flexmock(module).should_receive('find_databases_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='foo',
    ).and_return(('postgresql_databases', {'name': 'foo'}))
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='bar',
    ).and_return((None, None))
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='bar',
        configuration_database_name='all',
    ).and_return((None, None))
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'foo'},
    ).once()
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'bar'},
    ).never()
    flexmock(module).should_receive('ensure_databases_found')

    module.run_restore(
        repository='repo',
        location=flexmock(),
        storage=flexmock(),
        hooks=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', databases=flexmock()),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )


def test_run_restore_restores_databases_from_different_hooks():
    restore_names = {
        'postgresql_databases': ['foo'],
        'mysql_databases': ['bar'],
    }

    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').and_return(True)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks_even_if_unconfigured')
    flexmock(module.borgmatic.borg.rlist).should_receive('resolve_archive_name').and_return(
        flexmock()
    )
    flexmock(module).should_receive('collect_archive_database_names').and_return(flexmock())
    flexmock(module).should_receive('find_databases_to_restore').and_return(restore_names)
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='postgresql_databases',
        database_name='foo',
    ).and_return(('postgresql_databases', {'name': 'foo'}))
    flexmock(module).should_receive('get_configured_database').with_args(
        hooks=object,
        archive_database_names=object,
        hook_name='mysql_databases',
        database_name='bar',
    ).and_return(('mysql_databases', {'name': 'bar'}))
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='postgresql_databases',
        database={'name': 'foo'},
    ).once()
    flexmock(module).should_receive('restore_single_database').with_args(
        repository=object,
        location=object,
        storage=object,
        hooks=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        archive_name=object,
        hook_name='mysql_databases',
        database={'name': 'bar'},
    ).once()
    flexmock(module).should_receive('ensure_databases_found')

    module.run_restore(
        repository='repo',
        location=flexmock(),
        storage=flexmock(),
        hooks=flexmock(),
        local_borg_version=flexmock(),
        restore_arguments=flexmock(repository='repo', archive='archive', databases=flexmock()),
        global_arguments=flexmock(dry_run=False),
        local_path=flexmock(),
        remote_path=flexmock(),
    )
