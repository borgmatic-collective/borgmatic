from collections import OrderedDict

from flexmock import flexmock

from atticmatic import attic as module


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock()
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()
    flexmock(module).subprocess = subprocess


def insert_platform_mock():
    flexmock(module).platform = flexmock().should_receive('node').and_return('host').mock


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

    result = module.make_prune_flags(retention_config)

    assert tuple(result) == BASE_PRUNE_FLAGS


def test_prune_archives_should_call_attic_with_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('make_prune_flags').with_args(retention_config).and_return(
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
    flexmock(module).should_receive('make_prune_flags').with_args(retention_config).and_return(
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


def test_check_archives_should_call_attic_with_parameters():
    stdout = flexmock()
    insert_subprocess_mock(
        ('attic', 'check', 'repo'),
        stdout=stdout,
    )
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module).open = lambda filename, mode: stdout
    flexmock(module).os = flexmock().should_receive('devnull').mock

    module.check_archives(
        verbose=False,
        repository='repo',
    )


def test_check_archives_with_verbose_should_call_attic_with_verbose_parameters():
    insert_subprocess_mock(
        ('attic', 'check', 'repo', '--verbose'),
        stdout=None,
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.check_archives(
        verbose=True,
        repository='repo',
    )
