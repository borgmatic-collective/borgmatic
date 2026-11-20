import pytest
from flexmock import flexmock

from borgmatic.actions.check import frequency as module
from borgmatic.borg.pattern import Pattern


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
        module.datetime.timedelta(hours=1),
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('probe_for_check_time').and_return(
        module.datetime.datetime(year=module.datetime.MINYEAR, month=1, day=1),
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
        module.datetime.timedelta(hours=1),
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
        module.datetime.timedelta(hours=1),
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('probe_for_check_time').and_return(
        module.datetime.datetime.now(),
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


def test_make_check_time_path_with_borgmatic_source_directory_includes_it():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return(
        '/home/user/.local/state/borgmatic',
    )

    assert (
        module.make_check_time_path({}, '1234', 'archives', '5678')
        == '/home/user/.local/state/borgmatic/checks/1234/archives/5678'
    )


def test_make_check_time_path_with_archives_check_and_no_archives_check_id_defaults_to_all():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
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
        'get_borgmatic_state_directory',
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
        '~/.borgmatic/checks/1234/archives/5678',
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(1).and_return(2)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 2


def test_probe_for_check_time_deduplicates_identical_check_time_paths():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678',
    ).and_return('~/.borgmatic/checks/1234/archives/5678')
    flexmock(module).should_receive('read_check_time').and_return(1).once()

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 1


def test_probe_for_check_time_skips_none_check_time():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678',
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(None).and_return(2)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 2


def test_probe_for_check_time_uses_single_check_time():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678',
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(1).and_return(None)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) == 1


def test_probe_for_check_time_returns_none_when_no_check_time_found():
    flexmock(module).should_receive('make_check_time_path').and_return(
        '~/.borgmatic/checks/1234/archives/5678',
    ).and_return('~/.borgmatic/checks/1234/archives/all')
    flexmock(module).should_receive('read_check_time').and_return(None).and_return(None)

    assert module.probe_for_check_time(flexmock(), flexmock(), flexmock(), flexmock()) is None


def test_upgrade_check_times_moves_checks_from_borgmatic_source_directory_to_state_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.borgmatic/checks',
    ).and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.local/state/borgmatic/checks',
    ).and_return(False)
    flexmock(module.os).should_receive('makedirs')
    flexmock(module.shutil).should_receive('move').with_args(
        '/home/user/.borgmatic/checks',
        '/home/user/.local/state/borgmatic/checks',
    ).once()

    flexmock(module).should_receive('make_check_time_path').and_return(
        '/home/user/.local/state/borgmatic/checks/1234/archives/all',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_with_checks_already_in_borgmatic_state_directory_does_not_move_anything():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.borgmatic/checks',
    ).and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args(
        '/home/user/.local/state/borgmatic/checks',
    ).and_return(True)
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module.shutil).should_receive('move').never()

    flexmock(module).should_receive('make_check_time_path').and_return(
        '/home/user/.local/state/borgmatic/checks/1234/archives/all',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.shutil).should_receive('move').never()
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_old_check_paths_to_all():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    base_path = '/home/user/.local/state/borgmatic/checks/1234'
    flexmock(module).should_receive('make_check_time_path').with_args(
        object,
        object,
        'archives',
        'all',
    ).and_return(f'{base_path}/archives/all')
    flexmock(module).should_receive('make_check_time_path').with_args(
        object,
        object,
        'data',
        'all',
    ).and_return(f'{base_path}/data/all')
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/archives').and_return(
        True,
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/archives.temp',
    ).and_return(False)
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/data').and_return(
        False,
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/data.temp',
    ).and_return(False)
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives',
        f'{base_path}/archives.temp',
    ).once()
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/archives').once()
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives.temp',
        f'{base_path}/archives/all',
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_data_check_paths_when_archives_paths_are_already_upgraded():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    base_path = '/home/user/.local/state/borgmatic/checks/1234'
    flexmock(module).should_receive('make_check_time_path').with_args(
        object,
        object,
        'archives',
        'all',
    ).and_return(f'{base_path}/archives/all')
    flexmock(module).should_receive('make_check_time_path').with_args(
        object,
        object,
        'data',
        'all',
    ).and_return(f'{base_path}/data/all')
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/archives').and_return(
        False,
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/archives.temp',
    ).and_return(False)
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/data').and_return(
        True,
    )
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/data',
        f'{base_path}/data.temp',
    ).once()
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/data').once()
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/data.temp',
        f'{base_path}/data/all',
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_skips_already_upgraded_check_paths():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    flexmock(module).should_receive('make_check_time_path').and_return(
        '/home/user/.local/state/borgmatic/checks/1234/archives/all',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(False)
    flexmock(module.shutil).should_receive('move').never()
    flexmock(module.os).should_receive('mkdir').never()

    module.upgrade_check_times(flexmock(), flexmock())


def test_upgrade_check_times_renames_stale_temporary_check_path():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_state_directory',
    ).and_return('/home/user/.local/state/borgmatic')
    flexmock(module.os.path).should_receive('exists').and_return(False)

    base_path = '/home/borgmatic/.local/state/checks/1234'
    flexmock(module).should_receive('make_check_time_path').with_args(
        object,
        object,
        'archives',
        'all',
    ).and_return(f'{base_path}/archives/all')
    flexmock(module).should_receive('make_check_time_path').with_args(
        object,
        object,
        'data',
        'all',
    ).and_return(f'{base_path}/data/all')
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/archives').and_return(
        False,
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/archives.temp',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isfile').with_args(f'{base_path}/data').and_return(
        False,
    )
    flexmock(module.os.path).should_receive('isfile').with_args(
        f'{base_path}/data.temp',
    ).and_return(False)
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives',
        f'{base_path}/archives.temp',
    ).and_raise(FileNotFoundError)
    flexmock(module.os).should_receive('mkdir').with_args(f'{base_path}/archives').once()
    flexmock(module.shutil).should_receive('move').with_args(
        f'{base_path}/archives.temp',
        f'{base_path}/archives/all',
    ).once()

    module.upgrade_check_times(flexmock(), flexmock())
