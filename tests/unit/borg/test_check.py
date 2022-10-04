import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import check as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        command, extra_environment=None
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
    'frequency', ('sometime', 'x days', '3 decades',),
)
def test_parse_frequency_raises_on_parse_error(frequency):
    with pytest.raises(ValueError):
        module.parse_frequency(frequency)


def test_filter_checks_on_frequency_without_config_uses_default_checks():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(weeks=4)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('read_check_time').and_return(None)

    assert module.filter_checks_on_frequency(
        location_config={},
        consistency_config={},
        borg_repository_id='repo',
        checks=('repository', 'archives'),
        force=False,
    ) == ('repository', 'archives')


def test_filter_checks_on_frequency_retains_unconfigured_check():
    assert module.filter_checks_on_frequency(
        location_config={},
        consistency_config={},
        borg_repository_id='repo',
        checks=('data',),
        force=False,
    ) == ('data',)


def test_filter_checks_on_frequency_retains_check_without_frequency():
    flexmock(module).should_receive('parse_frequency').and_return(None)

    assert module.filter_checks_on_frequency(
        location_config={},
        consistency_config={'checks': [{'name': 'archives'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_elapsed_frequency():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(hours=1)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('read_check_time').and_return(
        module.datetime.datetime(year=module.datetime.MINYEAR, month=1, day=1)
    )

    assert module.filter_checks_on_frequency(
        location_config={},
        consistency_config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
    ) == ('archives',)


def test_filter_checks_on_frequency_retains_check_with_missing_check_time_file():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(hours=1)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('read_check_time').and_return(None)

    assert module.filter_checks_on_frequency(
        location_config={},
        consistency_config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=False,
    ) == ('archives',)


def test_filter_checks_on_frequency_skips_check_with_unelapsed_frequency():
    flexmock(module).should_receive('parse_frequency').and_return(
        module.datetime.timedelta(hours=1)
    )
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('read_check_time').and_return(module.datetime.datetime.now())

    assert (
        module.filter_checks_on_frequency(
            location_config={},
            consistency_config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
            borg_repository_id='repo',
            checks=('archives',),
            force=False,
        )
        == ()
    )


def test_filter_checks_on_frequency_restains_check_with_unelapsed_frequency_and_force():
    assert module.filter_checks_on_frequency(
        location_config={},
        consistency_config={'checks': [{'name': 'archives', 'frequency': '1 hour'}]},
        borg_repository_id='repo',
        checks=('archives',),
        force=True,
    ) == ('archives',)


def test_make_check_flags_with_repository_check_returns_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('repository',))

    assert flags == ('--repository-only',)


def test_make_check_flags_with_archives_check_returns_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('archives',))

    assert flags == ('--archives-only',)


def test_make_check_flags_with_data_check_returns_flag_and_implies_archives():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('data',))

    assert flags == ('--archives-only', '--verify-data',)


def test_make_check_flags_with_extract_omits_extract_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('extract',))

    assert flags == ()


def test_make_check_flags_with_repository_and_data_checks_does_not_return_repository_only():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('repository', 'data',))

    assert flags == ('--verify-data',)


def test_make_check_flags_with_default_checks_and_default_prefix_returns_default_flags():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags(
        '1.2.3', ('repository', 'archives'), prefix=module.DEFAULT_PREFIX
    )

    assert flags == ('--match-archives', f'sh:{module.DEFAULT_PREFIX}*')


def test_make_check_flags_with_all_checks_and_default_prefix_returns_default_flags():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags(
        '1.2.3', ('repository', 'archives', 'extract'), prefix=module.DEFAULT_PREFIX
    )

    assert flags == ('--match-archives', f'sh:{module.DEFAULT_PREFIX}*')


def test_make_check_flags_with_all_checks_and_default_prefix_without_borg_features_returns_glob_archives_flags():
    flexmock(module.feature).should_receive('available').and_return(False)

    flags = module.make_check_flags(
        '1.2.3', ('repository', 'archives', 'extract'), prefix=module.DEFAULT_PREFIX
    )

    assert flags == ('--glob-archives', f'{module.DEFAULT_PREFIX}*')


def test_make_check_flags_with_archives_check_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('archives',), check_last=3)

    assert flags == ('--archives-only', '--last', '3')


def test_make_check_flags_with_repository_check_and_last_omits_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('repository',), check_last=3)

    assert flags == ('--repository-only',)


def test_make_check_flags_with_default_checks_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('repository', 'archives'), check_last=3)

    assert flags == ('--last', '3')


def test_make_check_flags_with_archives_check_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('archives',), prefix='foo-')

    assert flags == ('--archives-only', '--match-archives', 'sh:foo-*')


def test_make_check_flags_with_archives_check_and_empty_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('archives',), prefix='')

    assert flags == ('--archives-only',)


def test_make_check_flags_with_archives_check_and_none_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('archives',), prefix=None)

    assert flags == ('--archives-only',)


def test_make_check_flags_with_repository_check_and_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('repository',), prefix='foo-')

    assert flags == ('--repository-only',)


def test_make_check_flags_with_default_checks_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    flags = module.make_check_flags('1.2.3', ('repository', 'archives'), prefix='foo-')

    assert flags == ('--match-archives', 'sh:foo-*')


def test_read_check_time_does_not_raise():
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_mtime=123))

    assert module.read_check_time('/path')


def test_read_check_time_on_missing_file_does_not_raise():
    flexmock(module.os).should_receive('stat').and_raise(FileNotFoundError)

    assert module.read_check_time('/path') is None


def test_check_archives_with_progress_calls_borg_with_progress_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--progress', 'repo'),
        output_file=module.DO_NOT_CAPTURE,
        extra_environment=None,
    ).once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
        progress=True,
    )


def test_check_archives_with_repair_calls_borg_with_repair_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--repair', 'repo'),
        output_file=module.DO_NOT_CAPTURE,
        extra_environment=None,
    ).once()
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
        repair=True,
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
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').with_args(
        '1.2.3', checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_with_json_error_raises():
    checks = ('archives',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"unexpected": {"id": "repo"}}'
    )

    with pytest.raises(ValueError):
        module.check_archives(
            repository='repo',
            location_config={},
            storage_config={},
            consistency_config=consistency_config,
            local_borg_version='1.2.3',
        )


def test_check_archives_with_missing_json_keys_raises():
    checks = ('archives',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return('{invalid JSON')

    with pytest.raises(ValueError):
        module.check_archives(
            repository='repo',
            location_config={},
            storage_config={},
            consistency_config=consistency_config,
            local_borg_version='1.2.3',
        )


def test_check_archives_with_extract_check_calls_extract_only():
    checks = ('extract',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').never()
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.extract).should_receive('extract_last_archive_dry_run').once()
    flexmock(module).should_receive('write_check_time')
    insert_execute_command_never()

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_with_log_info_calls_borg_with_info_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_logging_mock(logging.INFO)
    insert_execute_command_mock(('borg', 'check', '--info', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_with_log_debug_calls_borg_with_debug_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_logging_mock(logging.DEBUG)
    insert_execute_command_mock(('borg', 'check', '--debug', '--show-rc', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_without_any_checks_bails():
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(())
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    insert_execute_command_never()

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_with_local_path_calls_borg_via_local_path():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').with_args(
        '1.2.3', checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1', 'check', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
        local_path='borg1',
    )


def test_check_archives_with_remote_path_calls_borg_with_remote_path_parameters():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').with_args(
        '1.2.3', checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--remote-path', 'borg1', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
        remote_path='borg1',
    )


def test_check_archives_with_lock_wait_calls_borg_with_lock_wait_parameters():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').with_args(
        '1.2.3', checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--lock-wait', '5', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={'lock_wait': 5},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_with_retention_prefix():
    checks = ('repository',)
    check_last = flexmock()
    prefix = 'foo-'
    consistency_config = {'check_last': check_last, 'prefix': prefix}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').with_args(
        '1.2.3', checks, check_last, prefix
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )


def test_check_archives_with_extra_borg_options_calls_borg_with_extra_options():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('parse_checks')
    flexmock(module).should_receive('filter_checks_on_frequency').and_return(checks)
    flexmock(module.rinfo).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )
    flexmock(module).should_receive('make_check_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--extra', '--options', 'repo'))
    flexmock(module).should_receive('make_check_time_path')
    flexmock(module).should_receive('write_check_time')

    module.check_archives(
        repository='repo',
        location_config={},
        storage_config={'extra_borg_options': {'check': '--extra --options'}},
        consistency_config=consistency_config,
        local_borg_version='1.2.3',
    )
