from flexmock import flexmock
import pytest

from borgmatic.actions import check as module


def test_parse_checks_returns_them_as_tuple():
    checks = module.parse_checks({'checks': [{'name': 'foo'}, {'name': 'bar'}]})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module.parse_checks({})

    assert checks == ('repository', 'archives')


def test_parse_checks_with_empty_list_returns_defaults():
    checks = module.parse_checks({'checks': []})

    assert checks == ('repository', 'archives')


def test_parse_checks_with_none_value_returns_defaults():
    checks = module.parse_checks({'checks': None})

    assert checks == ('repository', 'archives')


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module.parse_checks({'checks': [{'name': 'foo'}, {'name': 'disabled'}]})

    assert checks == ()


def test_parse_checks_prefers_override_checks_to_configured_checks():
    checks = module.parse_checks(
        {'checks': [{'name': 'archives'}]}, only_checks=['repository', 'extract']
    )

    assert checks == ('repository', 'extract')


@pytest.mark.parametrize(
    'frequency,expected_result',
    (
        (None, None),
        ('always', None),
        ('1 hour', module.datetime.timedelta(hours=1)),
        ('2 hours', module.datetime.timedelta(hours=2)),
        ('1 day', module.datetime.timedelta(days=1)),
        ('2 days', module.datetime.timedelta(days=2)),
        ('1 week', module.datetime.timedelta(weeks=1)),
        ('2 weeks', module.datetime.timedelta(weeks=2)),
        ('1 month', module.datetime.timedelta(days=30)),
        ('2 months', module.datetime.timedelta(days=60)),
        ('1 year', module.datetime.timedelta(days=365)),
        ('2 years', module.datetime.timedelta(days=365 * 2)),
    ),
)
def test_parse_frequency_parses_into_timedeltas(frequency, expected_result):
    assert module.parse_frequency(frequency) == expected_result


@pytest.mark.parametrize(
    'frequency',
    (
        'sometime',
        'x days',
        '3 decades',
    ),
)
def test_parse_frequency_raises_on_parse_error(frequency):
    with pytest.raises(ValueError):
        module.parse_frequency(frequency)


def test_filter_checks_on_frequency_without_config_uses_default_checks():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(weeks=4)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('probe_for_check_time').and_return(None)

    assert module.filter_checks_on_frequency(
        config={},
        borg_repository_id='repo',
        checks=('repository', 'archives'),
        force=False,
        archives_check_id='1234',
    ) == ('repository', 'archives')


def test_filter_checks_on_frequency_retains_unconfigured_check():
    assert module.filter_checks_on_frequency(
        config={},
        borg_repository_id='repo',
        checks=('data',),
        force=False,
    ) == ('data',)


def test_filter_checks_on_frequency_retains_check_without_frequency():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_elapsed_frequency():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(hours=1)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('probe_for_check_time').and_return(
        module.datetime.datetime(year=module.datetime.MINYEAR, month=1, day=1)
    )

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_missing_check_time_file():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(hours=1)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('probe_for_check_time').and_return(None)

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
    ) == ('archives',)


def test_filter_checks_on_frequency_skips_check_with_unelapsed_frequency():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(hours=1)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('probe_for_check_time').and_return(
        module.datetime.datetime.now()
    )

    assert (
        module.filter_checks_on_frequency(
            config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
            borg_repository_id='repo',
            checks=('archives',),
            force=False,
            archives_check_id='1234',
        )
        == ()
    )


def test_filter_checks_on_frequency_restains_check_with_unelapsed_frequency_and_force():
    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=True,
        archives_check_id='1234',
    ) == ('archives',)


def test_filter_checks_on_frequency_passes_through_empty_checks():
    assert (
        module.filter_checks_on_frequency(
            config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
            borg_repository_id='repo',
            checks=(),
            force=False,
            archives_check_id='1234',
        )
        == ()
    )


def test_make_archives_check_id_with_flags_returns_a_value_and_does_not_raise():
    assert module.make_archives_check_id(('--match-archives', 'sh:foo-*'))


def test_make_archives_check_id_with_empty_flags_returns_none():
    assert module.make_archives_check_id(()) is None


def test_make_check_time_path_with_borgmatic_source_directory_includes_it():
    flexmock(module.os.path).should_receive('expanduser').with_args('~/.borgmatic').and_return(
        '/home/user/.borgmatic'
    )

    assert (
        module.make_check_time_path(
            {'borgmatic_source_directory': '~/.borgmatic'}, '1234', 'archives', '5678'
        )
        == '/home/user/.borgmatic/checks/1234/archives/5678'
    )


def test_make_check_time_path_without_borgmatic_source_directory_uses_default():
    flexmock(module.os.path).should_receive('expanduser').with_args(
        module.borgmatic.borg.state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY
    ).and_return('/home/user/.borgmatic')

    assert (
        module.make_check_time_path({}, '1234', 'archives', '5678')
        == '/home/user/.borgmatic/checks/1234/archives/5678'
    )


def test_make_check_time_path_with_archives_check_and_no_archives_check_id_defaults_to_all():
    flexmock(module.os.path).should_receive('expanduser').with_args('~/.borgmatic').and_return(
        '/home/user/.borgmatic'
    )

    assert (
        module.make_check_time_path(
            {'borgmatic_source_directory': '~/.borgmatic'},
            '1234',
            'archives',
        )
        == '/home/user/.borgmatic/checks/1234/archives/all'
    )


def test_make_check_time_path_with_repositories_check_ignores_archives_check_id():
    flexmock(module.os.path).should_receive('expanduser').with_args('~/.borgmatic').and_return(
        '/home/user/.borgmatic'
    )

    assert (
        module.make_check_time_path(
            {'borgmatic_source_directory': '~/.borgmatic'}, '1234', 'repository', '5678'
        )
        == '/home/user/.borgmatic/checks/1234/repository'
    )


def test_read_check_time_does_not_raise():
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_mtime=123))

    assert module.read_check_time('/path')


def test_read_check_time_on_missing_file_does_not_raise():
    flexmock(module.os).should_receive('stat').and_raise(FileNotFoundError)

    assert module.read_check_time('/path') is None


def test_probe_for_check_time_uses_maximum_of_multiple_check_times():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678'
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(1).and_return(2)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 2


def test_probe_for_check_time_deduplicates_identical_check_time_paths():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678'
    ).and_return('~/.borgmatic/checks/1234/archives/5678')
    flexmock(module).should_receive('read_check_time').and_return(1).once()

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 1


def test_probe_for_check_time_skips_none_check_time():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678'
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(None).and_return(2)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 2


def test_probe_for_check_time_uses_single_check_time():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678'
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(1).and_return(None)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 1


def test_probe_for_check_time_returns_none_when_no_check_time_found():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678'
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(None).and_return(None)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) is None


def test_upgrade_check_times_renames_old_check_paths_to_all():
    base_path = '~/.borgmatic/checks/1234'
    flexmock(module).should_receive('make_check_time_path').with_args(
        object, object, 'archives', 'all'
    ).and_return(f'{base_path}/archives/all')
    flexmock(module).should_receive('make_check_time_path').with_args(
        object, object, 'data', 'all'
    ).and_return(f'{base_path}/data/all')
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/archives').and_return(
        True
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/archives.temp'
    ).and_return(False)
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/data').and_return(
        False
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/data.temp'
    ).and_return(False)
    flexmock(module.os).should_receive('rename').with_args(
        f'{base_path}/archives', f'{base_path}/archives.temp'
    ).once()
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/archives').once()
    flexmock(module.os).should_receive('rename').with_args(
        f'{base_path}/archives.temp', f'{base_path}/archives/all'
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_data_check_paths_when_archives_paths_are_already_upgraded():
    base_path = '~/.borgmatic/checks/1234'
    flexmock(module).should_receive('make_check_time_path').with_args(
        object, object, 'archives', 'all'
    ).and_return(f'{base_path}/archives/all')
    flexmock(module).should_receive('make_check_time_path').with_args(
        object, object, 'data', 'all'
    ).and_return(f'{base_path}/data/all')
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/archives').and_return(
        False
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/archives.temp'
    ).and_return(False)
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/data').and_return(
        True
    )
    flexmock(module.os).should_receive('rename').with_args(
        f'{base_path}/data', f'{base_path}/data.temp'
    ).once()
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/data').once()
    flexmock(module.os).should_receive('rename').with_args(
        f'{base_path}/data.temp', f'{base_path}/data/all'
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_skips_missing_check_paths():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/all'
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.os).should_receive('rename').never()
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_stale_temporary_check_path():
    base_path = '~/.borgmatic/checks/1234'
    flexmock(module).should_receive('make_check_time_path').with_args(
        object, object, 'archives', 'all'
    ).and_return(f'{base_path}/archives/all')
    flexmock(module).should_receive('make_check_time_path').with_args(
        object, object, 'data', 'all'
    ).and_return(f'{base_path}/data/all')
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/archives').and_return(
        False
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/archives.temp'
    ).and_return(True)
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/data').and_return(
        False
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/data.temp'
    ).and_return(False)
    flexmock(module.os).should_receive('rename').with_args(
        f'{base_path}/archives', f'{base_path}/archives.temp'
    ).and_raise(FileNotFoundError)
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/archives').once()
    flexmock(module.os).should_receive('rename').with_args(
        f'{base_path}/archives.temp', f'{base_path}/archives/all'
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_run_check_checks_archives_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return({'repository', 'archives'})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=flexmock(),
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_runs_configured_extract_check():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return({'extract'})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=flexmock(),
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_without_checks_runs_nothing_except_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return({})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time').never()
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=flexmock(),
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_checks_archives_in_selected_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return({'repository', 'archives'})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
    check_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        repair=flexmock(),
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(False)
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    check_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        repair=flexmock(),
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        hook_context={},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
