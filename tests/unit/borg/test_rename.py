import logging

from flexmock import flexmock

from borgmatic.borg import rename as module


def test_rename_archive_calls_borg_rename():
    environment = flexmock()

    # Note: make_rename_command is tested as integration test.
    flexmock(module).should_receive('make_rename_command').and_return(('borg', 'fake-command'))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment,
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        ('borg', 'fake-command'),
        output_log_level=logging.INFO,
        environment=environment,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.rename_archive(
        dry_run=False,
        repository_name='repo',
        old_archive_name='old_archive',
        new_archive_name='new_archive',
        config={},
        local_borg_version='1.2.3',
        local_path='borg',
        remote_path=None,
    )
