from collections import OrderedDict

from flexmock import flexmock

from atticmatic import attic as module
from atticmatic.tests.builtins import builtins_mock


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock()
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()
    flexmock(module).subprocess = subprocess


def insert_subprocess_never():
    subprocess = flexmock()
    subprocess.should_receive('check_call').never()
    flexmock(module).subprocess = subprocess


def insert_platform_mock():
    flexmock(module.platform).should_receive('node').and_return('host')


def insert_datetime_mock():
    flexmock(module).datetime = flexmock().should_receive('now').and_return(
        flexmock().should_receive('isoformat').and_return('now').mock
    ).mock


def test_create_archive_should_call_attic_with_parameters():
    insert_subprocess_mock(
        ('attic', 'create', '--exclude-from', 'excludes', 'repo::host-now', 'foo', 'bar'),
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbose=False,
        source_directories='foo bar',
        repository='repo',
    )


def test_create_archive_with_verbose_should_call_attic_with_verbose_parameters():
    insert_subprocess_mock(
        (
            'attic', 'create', '--exclude-from', 'excludes', 'repo::host-now', 'foo', 'bar',
            '--verbose', '--stats',
        ),
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbose=True,
        source_directories='foo bar',
        repository='repo',
    )


BASE_PRUNE_FLAGS = (
    ('--keep-daily', '1'),
    ('--keep-weekly', '2'),
    ('--keep-monthly', '3'),
)


def test_make_prune_flags_should_return_flags_from_config():
    retention_config = OrderedDict(
        (
            ('keep_daily', 1),
            ('keep_weekly', 2),
            ('keep_monthly', 3),
        )
    )

    result = module._make_prune_flags(retention_config)

    assert tuple(result) == BASE_PRUNE_FLAGS


def test_prune_archives_should_call_attic_with_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(
        (
            'attic', 'prune', 'repo', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly',
            '3',
        ),
    )

    module.prune_archives(
        verbose=False,
        repository='repo',
        retention_config=retention_config,
    )


def test_prune_archives_with_verbose_should_call_attic_with_verbose_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(
        (
            'attic', 'prune', 'repo', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly',
            '3', '--verbose',
        ),
    )

    module.prune_archives(
        repository='repo',
        verbose=True,
        retention_config=retention_config,
    )


def test_parse_checks_returns_them_as_tuple():
    checks = module._parse_checks({'checks': 'foo disabled bar'})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module._parse_checks({})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_blank_value_returns_defaults():
    checks = module._parse_checks({'checks': ''})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module._parse_checks({'checks': 'disabled'})

    assert checks == ()


def test_make_check_flags_with_checks_returns_flags():
    flags = module._make_check_flags(('foo', 'bar'))

    assert flags == ('--foo-only', '--bar-only')


def test_make_check_flags_with_default_checks_returns_no_flags():
    flags = module._make_check_flags(module.DEFAULT_CHECKS)

    assert flags == ()


def test_check_archives_should_call_attic_with_parameters():
    consistency_config = flexmock()
    flexmock(module).should_receive('_parse_checks').and_return(flexmock())
    flexmock(module).should_receive('_make_check_flags').and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('attic', 'check', 'repo'),
        stdout=stdout,
    )
    insert_platform_mock()
    insert_datetime_mock()
    builtins_mock().should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        verbose=False,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_with_verbose_should_call_attic_with_verbose_parameters():
    consistency_config = flexmock()
    flexmock(module).should_receive('_parse_checks').and_return(flexmock())
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('attic', 'check', 'repo', '--verbose'),
        stdout=None,
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.check_archives(
        verbose=True,
        repository='repo',
        consistency_config=consistency_config,
    )


def test_check_archives_without_any_checks_should_bail():
    consistency_config = flexmock()
    flexmock(module).should_receive('_parse_checks').and_return(())
    insert_subprocess_never()

    module.check_archives(
        verbose=False,
        repository='repo',
        consistency_config=consistency_config,
    )
