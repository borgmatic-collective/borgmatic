import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import check as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command, borg_exit_codes=None):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command,
        extra_environment=None,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def insert_execute_command_never():
    flexmock(module).should_receive('execute_command').never()


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


def test_make_archive_filter_flags_with_default_checks_and_prefix_returns_default_flags():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {},
        ('repository', 'archives'),
        check_arguments=flexmock(match_archives=None),
        prefix='foo',
    )

    assert flags == ('--match-archives', 'sh:foo*')


def test_make_archive_filter_flags_with_all_checks_and_prefix_returns_default_flags():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {},
        ('repository', 'archives', 'extract'),
        check_arguments=flexmock(match_archives=None),
        prefix='foo',
    )

    assert flags == ('--match-archives', 'sh:foo*')


def test_make_archive_filter_flags_with_all_checks_and_prefix_without_borg_features_returns_glob_archives_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {},
        ('repository', 'archives', 'extract'),
        check_arguments=flexmock(match_archives=None),
        prefix='foo',
    )

    assert flags == ('--glob-archives', 'foo*')


def test_make_archive_filter_flags_with_archives_check_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('archives',), check_arguments=flexmock(match_archives=None), check_last=3
    )

    assert flags == ('--last', '3')


def test_make_archive_filter_flags_with_data_check_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('data',), check_arguments=flexmock(match_archives=None), check_last=3
    )

    assert flags == ('--last', '3')


def test_make_archive_filter_flags_with_repository_check_and_last_omits_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('repository',), check_arguments=flexmock(match_archives=None), check_last=3
    )

    assert flags == ()


def test_make_archive_filter_flags_with_default_checks_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {},
        ('repository', 'archives'),
        check_arguments=flexmock(match_archives=None),
        check_last=3,
    )

    assert flags == ('--last', '3')


def test_make_archive_filter_flags_with_archives_check_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('archives',), check_arguments=flexmock(match_archives=None), prefix='foo-'
    )

    assert flags == ('--match-archives', 'sh:foo-*')


def test_make_archive_filter_flags_with_data_check_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('data',), check_arguments=flexmock(match_archives=None), prefix='foo-'
    )

    assert flags == ('--match-archives', 'sh:foo-*')


def test_make_archive_filter_flags_prefers_check_arguments_match_archives_to_config_match_archives():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'baz-*', None, '1.2.3'
    ).and_return(('--match-archives', 'sh:baz-*'))

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'match_archives': 'bar-{now}'},  # noqa: FS003
        ('archives',),
        check_arguments=flexmock(match_archives='baz-*'),
        prefix='',
    )

    assert flags == ('--match-archives', 'sh:baz-*')


def test_make_archive_filter_flags_with_archives_check_and_empty_prefix_uses_archive_name_format_instead():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '1.2.3'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*'))

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'archive_name_format': 'bar-{now}'},  # noqa: FS003
        ('archives',),
        check_arguments=flexmock(match_archives=None),
        prefix='',
    )

    assert flags == ('--match-archives', 'sh:bar-*')


def test_make_archive_filter_flags_with_archives_check_and_none_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('archives',), check_arguments=flexmock(match_archives=None), prefix=None
    )

    assert flags == ()


def test_make_archive_filter_flags_with_repository_check_and_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3', {}, ('repository',), check_arguments=flexmock(match_archives=None), prefix='foo-'
    )

    assert flags == ()


def test_make_archive_filter_flags_with_default_checks_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {},
        ('repository', 'archives'),
        check_arguments=flexmock(match_archives=None),
        prefix='foo-',
    )

    assert flags == ('--match-archives', 'sh:foo-*')


def test_make_archives_check_id_with_flags_returns_a_value_and_does_not_raise():
    assert module.make_archives_check_id(('--match-archives', 'sh:foo-*'))


def test_make_archives_check_id_with_empty_flags_returns_none():
    assert module.make_archives_check_id(()) is None


def test_make_check_flags_with_repository_check_returns_flag():
    flags = module.make_check_flags(('repository',), ())

    assert flags == ('--repository-only',)


def test_make_check_flags_with_archives_check_returns_flag():
    flags = module.make_check_flags(('archives',), ())

    assert flags == ('--archives-only',)


def test_make_check_flags_with_archives_check_and_archive_filter_flags_includes_those_flags():
    flags = module.make_check_flags(('archives',), ('--match-archives', 'sh:foo-*'))

    assert flags == ('--archives-only', '--match-archives', 'sh:foo-*')


def test_make_check_flags_without_archives_check_and_with_archive_filter_flags_includes_those_flags():
    flags = module.make_check_flags(('repository',), ('--match-archives', 'sh:foo-*'))

    assert flags == ('--repository-only',)


def test_make_check_flags_with_data_check_returns_flag_and_implies_archives():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_check_flags(('data',), ())

    assert flags == (
        '--archives-only',
        '--verify-data',
    )


def test_make_check_flags_with_extract_omits_extract_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_check_flags(('extract',), ())

    assert flags == ()


def test_make_check_flags_with_repository_and_data_checks_does_not_return_repository_only():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_check_flags(
        (
            'repository',
            'data',
        ),
        (),
    )

    assert flags == ('--verify-data',)


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
        module.state.DEFAULT_BORGMATIC_SOURCE_DIRECTORY
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


def test_check_archives_with_progress_passes_through_to_borg():
    checks = ('repository',)
    config = {'check_last': None}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--progress', 'repo'),
        output_file=module.DO_NOT_CAPTURE,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=True, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_repair_passes_through_to_borg():
    checks = ('repository',)
    config = {'check_last': None}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--repair', 'repo'),
        output_file=module.DO_NOT_CAPTURE,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=True, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


@pytest.mark.parametrize(
    'checks',
    (
        ('repository',),
        ('archives',),
        ('repository', 'archives'),
        ('repository', 'archives', 'other'),
    ),
)
def test_check_archives_calls_borg_with_parameters(checks):
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_json_error_raises():
    checks = ('archives',)
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"unexpected": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)

    with pytest.raises(ValueError):
        module.check_archives(
            repository_path='repo',
            config=config,
            local_borg_version='1.2.3',
            check_arguments=flexmock(
                progress=None, repair=None, only_checks=None, force=None, match_archives=None
            ),
            global_arguments=flexmock(log_json=False),
        )


def test_check_archives_with_missing_json_keys_raises():
    checks = ('archives',)
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return('{invalid JSON')
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)

    with pytest.raises(ValueError):
        module.check_archives(
            repository_path='repo',
            config=config,
            local_borg_version='1.2.3',
            check_arguments=flexmock(
                progress=None, repair=None, only_checks=None, force=None, match_archives=None
            ),
            global_arguments=flexmock(log_json=False),
        )


def test_check_archives_with_extract_check_calls_extract_only():
    checks = ('extract',)
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').never()
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.extract).should_receive('extract_last_archive_dry_run').once()
    flexmock(module).should_receive('write_check_time')
    insert_execute_command_never()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_log_info_passes_through_to_borg():
    checks = ('repository',)
    config = {'check_last': None}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_logging_mock(logging.INFO)
    insert_execute_command_mock(('borg', 'check', '--info', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_log_debug_passes_through_to_borg():
    checks = ('repository',)
    config = {'check_last': None}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_logging_mock(logging.DEBUG)
    insert_execute_command_mock(('borg', 'check', '--debug', '--show-rc', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_without_any_checks_bails():
    config = {'check_last': None}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(())
    insert_execute_command_never()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_local_path_calls_borg_via_local_path():
    checks = ('repository',)
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1', 'check', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
        local_path='borg1',
    )


def test_check_archives_with_exit_codes_calls_borg_using_them():
    checks = ('repository',)
    check_last = flexmock()
    borg_exit_codes = flexmock()
    config = {'check_last': check_last, 'borg_exit_codes': borg_exit_codes}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'), borg_exit_codes=borg_exit_codes)
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_remote_path_passes_through_to_borg():
    checks = ('repository',)
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--remote-path', 'borg1', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
        remote_path='borg1',
    )


def test_check_archives_with_log_json_passes_through_to_borg():
    checks = ('repository',)
    check_last = flexmock()
    config = {'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--log-json', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=True),
    )


def test_check_archives_with_lock_wait_passes_through_to_borg():
    checks = ('repository',)
    check_last = flexmock()
    config = {'lock_wait': 5, 'check_last': check_last}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--lock-wait', '5', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_retention_prefix():
    checks = ('repository',)
    check_last = flexmock()
    prefix = 'foo-'
    config = {'check_last': check_last, 'prefix': prefix}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_extra_borg_options_passes_through_to_borg():
    checks = ('repository',)
    config = {'check_last': None, 'extra_borg_options': {'check': '--extra --options'}}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--extra', '--options', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )


def test_check_archives_with_match_archives_passes_through_to_borg():
    checks = ('archives',)
    config = {'check_last': None}
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('make_archive_filter_flags').and_return(
        ('--match-archives', 'foo-*')
    )
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module).should_receive('make_check_flags').and_return(('--match-archives', 'foo-*'))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--match-archives', 'foo-*', 'repo'),
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None, repair=None, only_checks=None, force=None, match_archives='foo-*'
        ),
        global_arguments=flexmock(log_json=False),
    )
