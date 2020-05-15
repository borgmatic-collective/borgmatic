import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import check as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(command):
    flexmock(module).should_receive('execute_command').with_args(command).once()


def insert_execute_command_never():
    flexmock(module).should_receive('execute_command').never()


def test_parse_checks_returns_them_as_tuple():
    checks = module._parse_checks({'checks': ['foo', 'disabled', 'bar']})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module._parse_checks({})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_blank_value_returns_defaults():
    checks = module._parse_checks({'checks': []})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_none_value_returns_defaults():
    checks = module._parse_checks({'checks': None})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module._parse_checks({'checks': ['disabled']})

    assert checks == ()


def test_parse_checks_with_data_check_also_injects_archives():
    checks = module._parse_checks({'checks': ['data']})

    assert checks == ('data', 'archives')


def test_parse_checks_with_data_check_passes_through_archives():
    checks = module._parse_checks({'checks': ['data', 'archives']})

    assert checks == ('data', 'archives')


def test_parse_checks_prefers_override_checks_to_configured_checks():
    checks = module._parse_checks({'checks': ['archives']}, only_checks=['repository', 'extract'])

    assert checks == ('repository', 'extract')


def test_parse_checks_with_override_data_check_also_injects_archives():
    checks = module._parse_checks({'checks': ['extract']}, only_checks=['data'])

    assert checks == ('data', 'archives')


def test_make_check_flags_with_repository_check_returns_flag():
    flags = module._make_check_flags(('repository',))

    assert flags == ('--repository-only',)


def test_make_check_flags_with_archives_check_returns_flag():
    flags = module._make_check_flags(('archives',))

    assert flags == ('--archives-only',)


def test_make_check_flags_with_data_check_returns_flag():
    flags = module._make_check_flags(('data',))

    assert flags == ('--verify-data',)


def test_make_check_flags_with_extract_omits_extract_flag():
    flags = module._make_check_flags(('extract',))

    assert flags == ()


def test_make_check_flags_with_default_checks_and_default_prefix_returns_default_flags():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, prefix=module.DEFAULT_PREFIX)

    assert flags == ('--prefix', module.DEFAULT_PREFIX)


def test_make_check_flags_with_all_checks_and_default_prefix_returns_default_flags():
    flags = module._make_check_flags(
        module.DEFAULT_CHECKS + ('extract',), prefix=module.DEFAULT_PREFIX
    )

    assert flags == ('--prefix', module.DEFAULT_PREFIX)


def test_make_check_flags_with_archives_check_and_last_includes_last_flag():
    flags = module._make_check_flags(('archives',), check_last=3)

    assert flags == ('--archives-only', '--last', '3')


def test_make_check_flags_with_repository_check_and_last_omits_last_flag():
    flags = module._make_check_flags(('repository',), check_last=3)

    assert flags == ('--repository-only',)


def test_make_check_flags_with_default_checks_and_last_includes_last_flag():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, check_last=3)

    assert flags == ('--last', '3')


def test_make_check_flags_with_archives_check_and_prefix_includes_prefix_flag():
    flags = module._make_check_flags(('archives',), prefix='foo-')

    assert flags == ('--archives-only', '--prefix', 'foo-')


def test_make_check_flags_with_archives_check_and_empty_prefix_omits_prefix_flag():
    flags = module._make_check_flags(('archives',), prefix='')

    assert flags == ('--archives-only',)


def test_make_check_flags_with_archives_check_and_none_prefix_omits_prefix_flag():
    flags = module._make_check_flags(('archives',), prefix=None)

    assert flags == ('--archives-only',)


def test_make_check_flags_with_repository_check_and_prefix_omits_prefix_flag():
    flags = module._make_check_flags(('repository',), prefix='foo-')

    assert flags == ('--repository-only',)


def test_make_check_flags_with_default_checks_and_prefix_includes_prefix_flag():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, prefix='foo-')

    assert flags == ('--prefix', 'foo-')


def test_check_archives_with_progress_calls_borg_with_progress_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    flexmock(module).should_receive('execute_command').never()
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--progress', 'repo'), output_file=module.DO_NOT_CAPTURE
    ).once()

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config, progress=True
    )


def test_check_archives_with_repair_calls_borg_with_repair_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    flexmock(module).should_receive('execute_command').never()
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--repair', 'repo'), output_file=module.DO_NOT_CAPTURE
    ).once()

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config, repair=True
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
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(
        checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    insert_execute_command_mock(('borg', 'check', 'repo'))

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_extract_check_calls_extract_only():
    checks = ('extract',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').never()
    flexmock(module.extract).should_receive('extract_last_archive_dry_run').once()
    insert_execute_command_never()

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_log_info_calls_borg_with_info_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_logging_mock(logging.INFO)
    insert_execute_command_mock(('borg', 'check', '--info', 'repo'))

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_log_debug_calls_borg_with_debug_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_logging_mock(logging.DEBUG)
    insert_execute_command_mock(('borg', 'check', '--debug', '--show-rc', 'repo'))

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_without_any_checks_bails():
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(())
    insert_execute_command_never()

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_local_path_calls_borg_via_local_path():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(
        checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    insert_execute_command_mock(('borg1', 'check', 'repo'))

    module.check_archives(
        repository='repo',
        storage_config={},
        consistency_config=consistency_config,
        local_path='borg1',
    )


def test_check_archives_with_remote_path_calls_borg_with_remote_path_parameters():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(
        checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    insert_execute_command_mock(('borg', 'check', '--remote-path', 'borg1', 'repo'))

    module.check_archives(
        repository='repo',
        storage_config={},
        consistency_config=consistency_config,
        remote_path='borg1',
    )


def test_check_archives_with_lock_wait_calls_borg_with_lock_wait_parameters():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(
        checks, check_last, module.DEFAULT_PREFIX
    ).and_return(())
    insert_execute_command_mock(('borg', 'check', '--lock-wait', '5', 'repo'))

    module.check_archives(
        repository='repo', storage_config={'lock_wait': 5}, consistency_config=consistency_config
    )


def test_check_archives_with_retention_prefix():
    checks = ('repository',)
    check_last = flexmock()
    prefix = 'foo-'
    consistency_config = {'check_last': check_last, 'prefix': prefix}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(
        checks, check_last, prefix
    ).and_return(())
    insert_execute_command_mock(('borg', 'check', 'repo'))

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_extra_borg_options_calls_borg_with_extra_options():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_execute_command_mock(('borg', 'check', '--extra', '--options', 'repo'))

    module.check_archives(
        repository='repo',
        storage_config={'extra_borg_options': {'check': '--extra --options'}},
        consistency_config=consistency_config,
    )
