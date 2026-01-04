import logging

from flexmock import flexmock

from borgmatic.borg import rename as module


def insert_logging_mock(log_level):
    '''
    Mock the isEnabledFor from Python logging.
    '''
    logging = flexmock(module.logging.Logger)
    logging.should_receive('isEnabledFor').replace_with(lambda level: level >= log_level)
    logging.should_receive('getEffectiveLevel').replace_with(lambda: log_level)


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

    assert command == ('borg', 'rename', '--info', '--log-json', 'repo::old_archive', 'new_archive')


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

    assert command == (
        'borg',
        'rename',
        '--debug',
        '--show-rc',
        '--log-json',
        'repo::old_archive',
        'new_archive',
    )


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

    assert command == (
        'borg',
        'rename',
        '--dry-run',
        '--log-json',
        'repo::old_archive',
        'new_archive',
    )


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
        '--log-json',
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

    assert command == (
        'borg',
        'rename',
        '--umask',
        '077',
        '--log-json',
        'repo::old_archive',
        'new_archive',
    )


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

    assert command == (
        'borg',
        'rename',
        '--log-json',
        '--lock-wait',
        '5',
        'repo::old_archive',
        'new_archive',
    )


def test_make_rename_command_includes_extra_borg_options():
    command = module.make_rename_command(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={'extra_borg_options': {'rename': '--extra "value with space"'}},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )

    assert command == (
        'borg',
        'rename',
        '--log-json',
        '--extra',
        'value with space',
        'repo::old_archive',
        'new_archive',
    )
