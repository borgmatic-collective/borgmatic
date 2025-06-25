import logging

from borgmatic.borg import rename as module
from tests.unit.test_verbosity import insert_logging_mock


def test_make_rename_command_includes_log_info():
    insert_logging_mock(logging.INFO)

    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'rename', '--info', 'repo::old_archive', 'new_archive')


def test_make_rename_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)

    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'rename', '--debug', '--show-rc', 'repo::old_archive', 'new_archive')


def test_make_rename_command_includes_dry_run():
    command = module.make_rename_command(
        dry_run=True,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'rename', '--dry-run', 'repo::old_archive', 'new_archive')


def test_make_rename_command_includes_remote_path():
    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path='borg1',
    )

    assert command == (
        'borg',
        'rename',
        '--remote-path',
        'borg1',
        'repo::old_archive',
        'new_archive',
    )


def test_make_rename_command_includes_umask():
    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={'umask': '077'},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'rename', '--umask', '077', 'repo::old_archive', 'new_archive')


def test_make_rename_command_includes_log_json():
    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={'log_json': True},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'rename', '--log-json', 'repo::old_archive', 'new_archive')


def test_make_rename_command_includes_lock_wait():
    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={'lock_wait': 5},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'rename', '--lock-wait', '5', 'repo::old_archive', 'new_archive')
