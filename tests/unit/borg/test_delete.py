import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import delete as module

from ..test_verbosity import insert_logging_mock


def test_make_delete_command_includes_log_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--info', 'repo')


def test_make_delete_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--debug', '--show-rc', 'repo')


def test_make_delete_command_includes_dry_run():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'dry-run', True
    ).and_return(('--dry-run',))
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=True),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--dry-run', 'repo')


def test_make_delete_command_includes_remote_path():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'remote-path', 'borg1'
    ).and_return(('--remote-path', 'borg1'))
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path='borg1',
    )

    assert command == ('borg', 'delete', '--remote-path', 'borg1', 'repo')


def test_make_delete_command_includes_umask():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else ()
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={'umask': '077'},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--umask', '077', 'repo')


def test_make_delete_command_includes_log_json():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'log-json', True
    ).and_return(('--log-json',))
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={'log_json': True},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--log-json', 'repo')


def test_make_delete_command_includes_lock_wait():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'lock-wait', 5
    ).and_return(('--lock-wait', '5'))
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={'lock_wait': 5},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--lock-wait', '5', 'repo')


def test_make_delete_command_with_list_config_calls_borg_with_list_flag():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').with_args(
        'list', True
    ).and_return(('--list',))
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={'list_details': True},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=None, force=0, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--list', 'repo')


def test_make_delete_command_includes_force():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=1, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--force', 'repo')


def test_make_delete_command_includes_force_twice():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(list_details=False, force=2, match_archives=None, archive=None),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--force', '--force', 'repo')


def test_make_delete_command_includes_archive():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(
        ('--match-archives', 'archive')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(
            list_details=False, force=0, match_archives=None, archive='archive'
        ),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--match-archives', 'archive', 'repo')


def test_make_delete_command_includes_match_archives():
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_match_archives_flags').and_return(
        ('--match-archives', 'sh:foo*')
    )
    flexmock(module.borgmatic.borg.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.borgmatic.borg.flags).should_receive('make_repository_flags').and_return(
        ('repo',)
    )

    command = module.make_delete_command(
        repository={'path': 'repo'},
        config={},
        local_borg_version='1.2.3',
        delete_arguments=flexmock(
            list_details=False, force=0, match_archives='sh:foo*', archive='archive'
        ),
        global_arguments=flexmock(dry_run=False),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'delete', '--match-archives', 'sh:foo*', 'repo')


LOGGING_ANSWER = flexmock()


def test_delete_archives_with_archive_calls_borg_delete():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository').never()
    flexmock(module).should_receive('make_delete_command').and_return(flexmock())
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').once()

    module.delete_archives(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        delete_arguments=flexmock(archive='archive'),
        global_arguments=flexmock(),
    )


def test_delete_archives_with_match_archives_calls_borg_delete():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository').never()
    flexmock(module).should_receive('make_delete_command').and_return(flexmock())
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').once()

    module.delete_archives(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        delete_arguments=flexmock(match_archives='sh:foo*'),
        global_arguments=flexmock(),
    )


@pytest.mark.parametrize('argument_name', module.ARCHIVE_RELATED_ARGUMENT_NAMES[2:])
def test_delete_archives_with_archive_related_argument_calls_borg_delete(argument_name):
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository').never()
    flexmock(module).should_receive('make_delete_command').and_return(flexmock())
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').once()

    module.delete_archives(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        delete_arguments=flexmock(archive='archive', **{argument_name: 'value'}),
        global_arguments=flexmock(),
    )


def test_delete_archives_without_archive_related_argument_calls_borg_repo_delete():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository').once()
    flexmock(module).should_receive('make_delete_command').never()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').never()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive('execute_command').never()

    module.delete_archives(
        repository={'path': 'repo'},
        config={},
        local_borg_version=flexmock(),
        delete_arguments=flexmock(
            list_details=True, force=False, cache_only=False, keep_security_info=False
        ),
        global_arguments=flexmock(),
    )


def test_delete_archives_calls_borg_delete_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = LOGGING_ANSWER
    flexmock(module.borgmatic.borg.repo_delete).should_receive('delete_repository').never()
    command = flexmock()
    flexmock(module).should_receive('make_delete_command').and_return(command)
    environment = flexmock()
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        environment
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir'
    )
    flexmock(module.borgmatic.execute).should_receive('execute_command').with_args(
        command,
        output_log_level=logging.ANSWER,
        environment=environment,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.delete_archives(
        repository={'path': 'repo'},
        config={'working_directory': '/working/dir'},
        local_borg_version=flexmock(),
        delete_arguments=flexmock(archive='archive'),
        global_arguments=flexmock(),
    )
