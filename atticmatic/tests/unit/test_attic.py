from flexmock import flexmock

from atticmatic import attic as module


def insert_subprocess_mock(check_call_command):
    subprocess = flexmock()
    subprocess.should_receive('check_call').with_args(check_call_command).once()
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


def test_prune_archives_should_call_attic_with_parameters():
    insert_subprocess_mock(
        (
            'attic', 'prune', 'repo', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly',
            '3',
        ),
    )

    module.prune_archives(
        repository='repo',
        verbose=False,
        keep_daily=1,
        keep_weekly=2,
        keep_monthly=3
    )


def test_prune_archives_with_verbose_should_call_attic_with_verbose_parameters():
    insert_subprocess_mock(
        (
            'attic', 'prune', 'repo', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly',
            '3', '--verbose',
        ),
    )

    module.prune_archives(
        repository='repo',
        verbose=True,
        keep_daily=1,
        keep_weekly=2,
        keep_monthly=3
    )
