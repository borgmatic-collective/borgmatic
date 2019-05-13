import logging
import sys

from flexmock import flexmock

from borgmatic.borg import extract as module

from ..test_verbosity import insert_logging_mock


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()


def insert_subprocess_never():
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').never()


def insert_subprocess_check_output_mock(check_output_command, result, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_output').with_args(check_output_command, **kwargs).and_return(
        result
    ).once()


def test_extract_last_archive_dry_run_calls_borg_with_last_archive():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo'), result='archive1\narchive2\n'.encode('utf-8')
    )
    insert_subprocess_mock(('borg', 'extract', '--dry-run', 'repo::archive2'))

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_without_any_archives_should_bail():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo'), result='\n'.encode('utf-8')
    )
    insert_subprocess_never()

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_with_log_info_calls_borg_with_info_parameter():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--info'), result='archive1\narchive2\n'.encode('utf-8')
    )
    insert_subprocess_mock(('borg', 'extract', '--dry-run', 'repo::archive2', '--info'))
    insert_logging_mock(logging.INFO)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--debug', '--show-rc'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive2', '--debug', '--show-rc', '--list')
    )
    insert_logging_mock(logging.DEBUG)

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None)


def test_extract_last_archive_dry_run_calls_borg_via_local_path():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg1', 'list', '--short', 'repo'), result='archive1\narchive2\n'.encode('utf-8')
    )
    insert_subprocess_mock(('borg1', 'extract', '--dry-run', 'repo::archive2'))

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None, local_path='borg1')


def test_extract_last_archive_dry_run_calls_borg_with_remote_path_parameters():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--remote-path', 'borg1'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(
        ('borg', 'extract', '--dry-run', 'repo::archive2', '--remote-path', 'borg1')
    )

    module.extract_last_archive_dry_run(repository='repo', lock_wait=None, remote_path='borg1')


def test_extract_last_archive_dry_run_calls_borg_with_lock_wait_parameters():
    flexmock(sys.stdout).encoding = 'utf-8'
    insert_subprocess_check_output_mock(
        ('borg', 'list', '--short', 'repo', '--lock-wait', '5'),
        result='archive1\narchive2\n'.encode('utf-8'),
    )
    insert_subprocess_mock(('borg', 'extract', '--dry-run', 'repo::archive2', '--lock-wait', '5'))

    module.extract_last_archive_dry_run(repository='repo', lock_wait=5)


def test_extract_archive_calls_borg_with_restore_path_parameters():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', 'path1', 'path2'))

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=['path1', 'path2'],
        location_config={},
        storage_config={},
    )


def test_extract_archive_calls_borg_with_remote_path_parameters():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--remote-path', 'borg1'))

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={},
        remote_path='borg1',
    )


def test_extract_archive_calls_borg_with_numeric_owner_parameter():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--numeric-owner'))

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={'numeric_owner': True},
        storage_config={},
    )


def test_extract_archive_calls_borg_with_umask_parameters():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--umask', '0770'))

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={'umask': '0770'},
    )


def test_extract_archive_calls_borg_with_lock_wait_parameters():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--lock-wait', '5'))

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={'lock_wait': '5'},
    )


def test_extract_archive_with_log_info_calls_borg_with_info_parameter():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--info'))
    insert_logging_mock(logging.INFO)

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={},
    )


def test_extract_archive_with_log_debug_calls_borg_with_debug_parameters():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--debug', '--list', '--show-rc'))
    insert_logging_mock(logging.DEBUG)

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={},
    )


def test_extract_archive_calls_borg_with_dry_run_parameter():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--dry-run'))

    module.extract_archive(
        dry_run=True,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={},
    )


def test_extract_archive_calls_borg_with_progress_parameter():
    insert_subprocess_mock(('borg', 'extract', 'repo::archive', '--progress'))

    module.extract_archive(
        dry_run=False,
        repository='repo',
        archive='archive',
        restore_paths=None,
        location_config={},
        storage_config={},
        progress=True,
    )
