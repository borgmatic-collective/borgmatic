import pytest
from flexmock import flexmock

from borgmatic.actions import check as module
from borgmatic.borg.pattern import Pattern


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


def test_filter_checks_on_frequency_retains_check_with_empty_only_run_on():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'only_run_on': []}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
        datetime_now=flexmock(weekday=lambda: 0),
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_only_run_on_matching_today():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'only_run_on': [module.calendar.day_name[0]]}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
        datetime_now=flexmock(weekday=lambda: 0),
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_only_run_on_matching_today_via_weekday_value():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'only_run_on': ['weekday']}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
        datetime_now=flexmock(weekday=lambda: 0),
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_only_run_on_matching_today_via_weekend_value():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert module.filter_checks_on_frequency(
        config={'checks': [{'name': 'archives', 'only_run_on': ['weekend']}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
        archives_check_id='1234',
        datetime_now=flexmock(weekday=lambda: 6),
    ) == ('archives',)


def test_filter_checks_on_frequency_skips_check_with_only_run_on_not_matching_today():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert (
        module.filter_checks_on_frequency(
            config={'checks': [{'name': 'archives', 'only_run_on': [module.calendar.day_name[5]]}]},
            borg_repository_id='repo',
            checks=('archives',),
            force=False,
            archives_check_id='1234',
            datetime_now=flexmock(weekday=lambda: 0),
        )
        == ()
    )


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


def test_filter_checks_on_frequency_retains_check_with_unelapsed_frequency_and_force():
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
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return(
        '/home/user/.local/state/borgmatic',
    )

    assert (
        module.make_check_time_path({}, '1234', 'archives', '5678')
        == '/home/user/.local/state/borgmatic/checks/1234/archives/5678'
    )


def test_make_check_time_path_with_archives_check_and_no_archives_check_id_defaults_to_all():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return(
        '/home/user/.local/state/borgmatic',
    )

    assert (
        module.make_check_time_path(
            {},
            '1234',
            'archives',
        )
        == '/home/user/.local/state/borgmatic/checks/1234/archives/all'
    )


def test_make_check_time_path_with_repositories_check_ignores_archives_check_id():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return(
        '/home/user/.local/state/borgmatic',
    )

    assert (
        module.make_check_time_path({}, '1234', 'repository', '5678')
        == '/home/user/.local/state/borgmatic/checks/1234/repository'
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


def test_upgrade_check_times_moves_checks_from_borgmatic_source_directory_to_state_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.borgmatic/checks'
    ).and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.local/state/borgmatic/checks'
    ).and_return(False)
    flexmock(module.os).should_receive('makedirs')
    flexmock(module.shutil).should_receive('move').with_args(
        '/home/user/.borgmatic/checks', '/home/user/.local/state/borgmatic/checks'
    ).once()

    flexmock(module).should_receive('make_check_time_path').and_return(
        '/home/user/.local/state/borgmatic/checks/1234/archives/all'
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_with_checks_already_in_borgmatic_state_directory_does_not_move_anything():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.borgmatic/checks'
    ).and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.local/state/borgmatic/checks'
    ).and_return(True)
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module.shutil).should_receive('move').never()

    flexmock(module).should_receive('make_check_time_path').and_return(
        '/home/user/.local/state/borgmatic/checks/1234/archives/all'
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.shutil).should_receive('move').never()
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_old_check_paths_to_all():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    base_path = '/home/user/.local/state/borgmatic/checks/1234'
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
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives', f'{base_path}/archives.temp'
    ).once()
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/archives').once()
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives.temp', f'{base_path}/archives/all'
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_data_check_paths_when_archives_paths_are_already_upgraded():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    base_path = '/home/user/.local/state/borgmatic/checks/1234'
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
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/data', f'{base_path}/data.temp'
    ).once()
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/data').once()
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/data.temp', f'{base_path}/data/all'
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_skips_already_upgraded_check_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    flexmock(module).should_receive('make_check_time_path').and_return(
        '/home/user/.local/state/borgmatic/checks/1234/archives/all'
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.shutil).should_receive('move').never()
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_stale_temporary_check_path():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory'
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    base_path = '/home/borgmatic/.local/state/checks/1234'
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
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives', f'{base_path}/archives.temp'
    ).and_raise(FileNotFoundError)
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/archives').once()
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives.temp', f'{base_path}/archives/all'
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_collect_spot_check_source_paths_parses_borg_output():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True}
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return(
        [Pattern('foo'), Pattern('bar')]
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'warning: stuff\n- /etc/path\n+ /etc/other\n? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_omits_progress_from_create_dry_run_command():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': False}
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return(
        [Pattern('foo'), Pattern('bar')]
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config={'working_directory': '/', 'list_details': True},
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=False,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'warning: stuff\n- /etc/path\n+ /etc/other\n? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/', 'progress': True},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_passes_through_stream_processes_false():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': False}
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return(
        [Pattern('foo'), Pattern('bar')]
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=False,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'warning: stuff\n- /etc/path\n+ /etc/other\n? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_without_working_directory_parses_borg_output():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True}
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return(
        [Pattern('foo'), Pattern('bar')]
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'warning: stuff\n- /etc/path\n+ /etc/other\n? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_skips_directories():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True}
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return(
        [Pattern('foo'), Pattern('bar')]
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'warning: stuff\n- /etc/path\n+ /etc/dir\n? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').with_args('/etc/path').and_return(False)
    flexmock(module.os.path).should_receive('isfile').with_args('/etc/dir').and_return(False)

    assert (
        module.collect_spot_check_source_paths(
            repository={'path': 'repo'},
            config={'working_directory': '/'},
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )
        == ()
    )


def test_collect_spot_check_archive_paths_excludes_directories_and_pipes():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        (
            'f etc/path',
            'p var/pipe',
            'f etc/other',
            'd etc/dir',
        )
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/1001/borgmatic',
    ) == ('etc/path', 'etc/other')


def test_collect_spot_check_archive_paths_excludes_file_in_borgmatic_runtime_directory_as_stored_with_prefix_truncation():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        (
            'f etc/path',
            'f borgmatic/some/thing',
        )
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/0/borgmatic',
    ) == ('etc/path',)


def test_collect_spot_check_archive_paths_excludes_file_in_borgmatic_source_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        (
            'f etc/path',
            'f root/.borgmatic/some/thing',
        )
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/0/borgmatic',
    ) == ('etc/path',)


def test_collect_spot_check_archive_paths_excludes_file_in_borgmatic_runtime_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory'
    ).and_return('/root.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        (
            'f etc/path',
            'f run/user/0/borgmatic/some/thing',
        )
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/0/borgmatic',
    ) == ('etc/path',)


def test_collect_spot_check_source_paths_uses_working_directory():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True}
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').and_return(
        [Pattern('foo'), Pattern('bar')]
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config={'working_directory': '/working/dir', 'list_details': True},
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir'
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).and_return(
        'warning: stuff\n- foo\n+ bar\n? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').with_args('/working/dir/foo').and_return(True)
    flexmock(module.os.path).should_receive('isfile').with_args('/working/dir/bar').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/working/dir'},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('foo', 'bar')


def test_compare_spot_check_hashes_returns_paths_having_failing_hashes():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_return(
        'hash1  /foo\nhash2  /bar'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'nothash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
    ) == ('/bar',)


def test_compare_spot_check_hashes_returns_relative_paths_having_failing_hashes():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', 'foo', 'bar'), working_directory=None).and_return(
        'hash1  foo\nhash2  bar'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'nothash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('foo', 'bar', 'baz', 'quux'),
    ) == ('bar',)


def test_compare_spot_check_hashes_handles_data_sample_percentage_above_100():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_return(
        'hash1  /foo\nhash2  /bar'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['nothash1 foo', 'nothash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 1000,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar'),
    ) == ('/foo', '/bar')


def test_compare_spot_check_hashes_uses_xxh64sum_command_option():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(
        ('/usr/local/bin/xxhsum', '-H64', '/foo', '/bar'), working_directory=None
    ).and_return(
        'hash1  /foo\nhash2  /bar'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'nothash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                    'xxh64sum_command': '/usr/local/bin/xxhsum -H64',
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
    ) == ('/bar',)


def test_compare_spot_check_hashes_considers_path_missing_from_archive_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_return(
        'hash1  /foo\nhash2  /bar'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
    ) == ('/bar',)


def test_compare_spot_check_hashes_considers_symlink_path_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').with_args('/foo').and_return(False)
    flexmock(module.os.path).should_receive('islink').with_args('/bar').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/foo'), working_directory=None).and_return('hash1  /foo')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'hash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
    ) == ('/bar',)


def test_compare_spot_check_hashes_considers_non_existent_path_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').with_args('/foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/bar').and_return(False)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/foo'), working_directory=None).and_return('hash1  /foo')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'hash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
    ) == ('/bar',)


def test_compare_spot_check_hashes_with_too_many_paths_feeds_them_to_commands_in_chunks():
    flexmock(module).SAMPLE_PATHS_SUBSET_COUNT = 2
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_return(
        'hash1  /foo\nhash2  /bar'
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', '/baz', '/quux'), working_directory=None).and_return(
        'hash3  /baz\nhash4  /quux'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'hash2 bar']
    ).and_return(['hash3 baz', 'nothash4 quux'])

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 100,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
    ) == ('/quux',)


def test_compare_spot_check_hashes_uses_working_directory_to_access_source_paths():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count])
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module.os.path).should_receive('exists').with_args('/working/dir/foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/working/dir/bar').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output'
    ).with_args(('xxh64sum', 'foo', 'bar'), working_directory='/working/dir').and_return(
        'hash1  foo\nhash2  bar'
    )
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_return(
        ['hash1 foo', 'nothash2 bar']
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
            'working_directory': '/working/dir',
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('foo', 'bar', 'baz', 'quux'),
    ) == ('bar',)


def test_spot_check_without_spot_configuration_errors():
    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'archives',
                    },
                ]
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_without_any_configuration_errors():
    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={},
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_data_tolerance_percentage_greater_than_data_sample_percentage_errors():
    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'data_tolerance_percentage': 7,
                        'data_sample_percentage': 5,
                    },
                ]
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_with_count_delta_greater_than_count_tolerance_percentage_errors():
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(
        ('/foo', '/bar', '/baz', '/quux')
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(
        ('/foo', '/bar')
    ).once()

    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'count_tolerance_percentage': 1,
                        'data_tolerance_percentage': 4,
                        'data_sample_percentage': 5,
                    },
                ]
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_with_failing_percentage_greater_than_data_tolerance_percentage_errors():
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(
        ('/foo', '/bar', '/baz', '/quux')
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(('/foo', '/bar'))
    flexmock(module).should_receive('compare_spot_check_hashes').and_return(
        ('/bar', '/baz', '/quux')
    ).once()

    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'count_tolerance_percentage': 55,
                        'data_tolerance_percentage': 4,
                        'data_sample_percentage': 5,
                    },
                ]
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_with_high_enough_tolerances_does_not_raise():
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(
        ('/foo', '/bar', '/baz', '/quux')
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(('/foo', '/bar'))
    flexmock(module).should_receive('compare_spot_check_hashes').and_return(
        ('/bar', '/baz', '/quux')
    ).once()

    module.spot_check(
        repository={'path': 'repo'},
        config={
            'checks': [
                {
                    'name': 'spot',
                    'count_tolerance_percentage': 55,
                    'data_tolerance_percentage': 80,
                    'data_sample_percentage': 80,
                },
            ]
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_spot_check_without_any_source_paths_errors():
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(())
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(('/foo', '/bar'))
    flexmock(module).should_receive('compare_spot_check_hashes').never()

    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'count_tolerance_percentage': 10,
                        'data_tolerance_percentage': 40,
                        'data_sample_percentage': 50,
                    },
                ]
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_run_check_checks_archives_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(
        {'repository', 'archives'}
    )
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
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
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_runs_configured_spot_check():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return({'spot'})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.check).should_receive('spot_check').once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')
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
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(
        {'repository', 'archives'}
    )
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
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
