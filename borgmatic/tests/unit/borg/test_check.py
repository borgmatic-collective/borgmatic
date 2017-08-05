from subprocess import STDOUT
import sys

from flexmock import flexmock
import pytest

from borgmatic.borg import check as module
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


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


def test_make_check_flags_with_checks_returns_flags():
    flags = module._make_check_flags(('repository',))

    assert flags == ('--repository-only',)


def test_make_check_flags_with_extract_check_does_not_make_extract_flag():
    flags = module._make_check_flags(('extract',))

    assert flags == ()


def test_make_check_flags_with_default_checks_returns_no_flags():
    flags = module._make_check_flags(module.DEFAULT_CHECKS)

    assert flags == ()


def test_make_check_flags_with_checks_and_last_returns_flags_including_last():
    flags = module._make_check_flags(('repository',), check_last=3)

    assert flags == ('--repository-only', '--last', '3')


def test_make_check_flags_with_default_checks_and_last_returns_last_flag():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, check_last=3)

    assert flags == ('--last', '3')


@pytest.mark.parametrize(
    'checks',
    (
        ('repository',),
        ('archives',),
        ('repository', 'archives'),
        ('repository', 'archives', 'other'),
    ),
)
def test_check_archives_should_call_borg_with_parameters(checks):
    check_last = flexmock()
    consistency_config = flexmock().should_receive('get').and_return(check_last).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(checks, check_last).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('borg', 'check', 'repo'),
        stdout=stdout, stderr=STDOUT,
    )
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_with_extract_check_should_call_extract_only():
    checks = ('extract',)
    check_last = flexmock()
    consistency_config = flexmock().should_receive('get').and_return(check_last).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').never()
    flexmock(module.extract).should_receive('extract_last_archive_dry_run').once()
    insert_subprocess_never()

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_with_verbosity_some_should_call_borg_with_info_parameter():
    checks = ('repository',)
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--info'),
        stdout=None, stderr=STDOUT,
    )

    module.check_archives(
        verbosity=VERBOSITY_SOME,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_with_verbosity_lots_should_call_borg_with_debug_parameter():
    checks = ('repository',)
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--debug'),
        stdout=None, stderr=STDOUT,
    )

    module.check_archives(
        verbosity=VERBOSITY_LOTS,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_without_any_checks_should_bail():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(())
    insert_subprocess_never()

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_with_remote_path_should_call_borg_with_remote_path_parameters():
    checks = ('repository',)
    check_last = flexmock()
    consistency_config = flexmock().should_receive('get').and_return(check_last).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(checks, check_last).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--remote-path', 'borg1'),
        stdout=stdout, stderr=STDOUT,
    )
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
        remote_path='borg1',
    )
