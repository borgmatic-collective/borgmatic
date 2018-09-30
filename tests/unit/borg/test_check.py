from subprocess import STDOUT
import logging
import sys

from flexmock import flexmock
import pytest

from borgmatic.borg import check as module
from ..test_verbosity import insert_logging_mock


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()


def insert_subprocess_never():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').never()


def test_parse_checks_returns_them_as_tuple():
    checks = module._parse_checks({'checks': ['foo', 'disabled', 'bar']})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module._parse_checks({})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_blank_value_returns_defaults():
    checks = module._parse_checks({'checks': []})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module._parse_checks({'checks': ['disabled']})

    assert checks == ()


def test_make_check_flags_with_repository_check_returns_flag():
    flags = module._make_check_flags(('repository',))

    assert flags == ('--repository-only',)


def test_make_check_flags_with_extract_omits_extract_flag():
    flags = module._make_check_flags(('extract',))

    assert flags == ()


def test_make_check_flags_with_default_checks_returns_default_flags():
    flags = module._make_check_flags(module.DEFAULT_CHECKS)

    assert flags == ('--prefix', module.DEFAULT_PREFIX)


def test_make_check_flags_with_all_checks_returns_default_flags():
    flags = module._make_check_flags(module.DEFAULT_CHECKS + ('extract',))

    assert flags == ('--prefix', module.DEFAULT_PREFIX)


def test_make_check_flags_with_archives_check_and_last_includes_last_flag():
    flags = module._make_check_flags(('archives',), check_last=3)

    assert flags == ('--archives-only', '--last', '3', '--prefix', module.DEFAULT_PREFIX)


def test_make_check_flags_with_repository_check_and_last_omits_last_flag():
    flags = module._make_check_flags(('repository',), check_last=3)

    assert flags == ('--repository-only',)


def test_make_check_flags_with_default_checks_and_last_includes_last_flag():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, check_last=3)

    assert flags == ('--last', '3', '--prefix', module.DEFAULT_PREFIX)


def test_make_check_flags_with_archives_check_and_prefix_includes_prefix_flag():
    flags = module._make_check_flags(('archives',), prefix='foo-')

    assert flags == ('--archives-only', '--prefix', 'foo-')


def test_make_check_flags_with_repository_check_and_prefix_omits_prefix_flag():
    flags = module._make_check_flags(('repository',), prefix='foo-')

    assert flags == ('--repository-only',)


def test_make_check_flags_with_default_checks_and_prefix_includes_prefix_flag():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, prefix='foo-')

    assert flags == ('--prefix', 'foo-')


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
        checks, check_last, None
    ).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(('borg', 'check', 'repo'), stdout=stdout, stderr=STDOUT)
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

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
    insert_subprocess_never()

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_log_info_calls_borg_with_info_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_logging_mock(logging.INFO)
    insert_subprocess_mock(('borg', 'check', 'repo', '--info'), stdout=None, stderr=STDOUT)

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_log_debug_calls_borg_with_debug_parameter():
    checks = ('repository',)
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_logging_mock(logging.DEBUG)
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--debug', '--show-rc'), stdout=None, stderr=STDOUT
    )

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_without_any_checks_bails():
    consistency_config = {'check_last': None}
    flexmock(module).should_receive('_parse_checks').and_return(())
    insert_subprocess_never()

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )


def test_check_archives_with_local_path_calls_borg_via_local_path():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = {'check_last': check_last}
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(
        checks, check_last, None
    ).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(('borg1', 'check', 'repo'), stdout=stdout, stderr=STDOUT)
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

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
        checks, check_last, None
    ).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--remote-path', 'borg1'), stdout=stdout, stderr=STDOUT
    )
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

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
        checks, check_last, None
    ).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--lock-wait', '5'), stdout=stdout, stderr=STDOUT
    )
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

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
    stdout = flexmock()
    insert_subprocess_mock(('borg', 'check', 'repo'), stdout=stdout, stderr=STDOUT)

    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        repository='repo', storage_config={}, consistency_config=consistency_config
    )
