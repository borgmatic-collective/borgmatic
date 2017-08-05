import sys

from flexmock import flexmock

from borgmatic.borg import extract as module
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()


def insert_subprocess_never():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').never()


def insert_subprocess_check_output_mock(check_output_command, result, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_output').with_args(check_output_command, **kwargs).and_return(result).once()


def test_extract_last_archive_dry_run_should_call_borg_with_last_archive():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive2'),
    )

    module.extract_last_archive_dry_run(
        verbosity=None,
        repository='repo',
    )


def test_extract_last_archive_dry_run_without_any_archives_should_bail():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo'),
        result='\n'.encode('utf-8'),
    )
    insert_subprocess_never()

    module.extract_last_archive_dry_run(
        verbosity=None,
        repository='repo',
    )


def test_extract_last_archive_dry_run_with_verbosity_some_should_call_borg_with_info_parameter():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--info'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive2', '--info'),
    )

    module.extract_last_archive_dry_run(
        verbosity=VERBOSITY_SOME,
        repository='repo',
    )


def test_extract_last_archive_dry_run_with_verbosity_lots_should_call_borg_with_debug_parameter():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--debug'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive2', '--debug', '--list'),
    )

    module.extract_last_archive_dry_run(
        verbosity=VERBOSITY_LOTS,
        repository='repo',
    )


def test_extract_last_archive_dry_run_should_call_borg_with_remote_path_parameters():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--remote-path', 'borg1'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive2', '--remote-path', 'borg1'),
    )

    module.extract_last_archive_dry_run(
        verbosity=None,
        repository='repo',
        remote_path='borg1',
    )
