import argparse
import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import repo_list as module

from ..test_verbosity import insert_logging_mock

BORG_LIST_LATEST_ARGUMENTS = (
    '--last',
    '1',
    '--short',
    'repo',
)


def test_resolve_archive_name_passes_through_non_latest_archive_name():
    archive = 'myhost-2030-01-01T14:41:17.647620'

    assert (
        module.resolve_archive_name(
            'repo',
            archive,
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == archive
    )


def test_resolve_archive_name_calls_borg_with_flags():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        borg_local_path='borg',
        borg_exit_codes=None,
        environment=None,
        working_directory=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_resolve_archive_name_with_log_info_calls_borg_without_info_flag():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')
    insert_logging_mock(logging.INFO)

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_resolve_archive_name_with_log_debug_calls_borg_without_debug_flag():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')
    insert_logging_mock(logging.DEBUG)

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_resolve_archive_name_with_local_path_calls_borg_via_local_path():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg1', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg1',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            local_path='borg1',
        )
        == expected_archive
    )


def test_resolve_archive_name_with_exit_codes_calls_borg_using_them():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    borg_exit_codes = flexmock()
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={'borg_exit_codes': borg_exit_codes},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_resolve_archive_name_with_remote_path_calls_borg_with_remote_path_flags():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', '--remote-path', 'borg1') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            remote_path='borg1',
        )
        == expected_archive
    )


def test_resolve_archive_name_with_umask_calls_borg_with_umask_flags():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', '--umask', '077') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={'umask': '077'},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_resolve_archive_name_without_archives_raises():
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return('')

    with pytest.raises(ValueError):
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )


def test_resolve_archive_name_with_log_json_calls_borg_with_log_json_flags():
    expected_archive = 'archive-name'

    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', '--log-json') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=True),
        )
        == expected_archive
    )


def test_resolve_archive_name_with_lock_wait_calls_borg_with_lock_wait_flags():
    expected_archive = 'archive-name'

    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', '--lock-wait', 'okay') + BORG_LIST_LATEST_ARGUMENTS,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={'lock_wait': 'okay'},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_resolve_archive_name_calls_borg_with_working_directory():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        borg_local_path='borg',
        borg_exit_codes=None,
        environment=None,
        working_directory='/working/dir',
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo',
            'latest',
            config={'working_directory': '/working/dir'},
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
        )
        == expected_archive
    )


def test_make_repo_list_command_includes_log_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--info', 'repo')


def test_make_repo_list_command_includes_json_but_not_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=True, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_repo_list_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--debug', '--show-rc', 'repo')


def test_make_repo_list_command_includes_json_but_not_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=True, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_repo_list_command_includes_json():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=True, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_repo_list_command_includes_log_json():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(
        ('--log-json',)
    ).and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=True),
    )

    assert command == ('borg', 'list', '--log-json', 'repo')


def test_make_repo_list_command_includes_lock_wait():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(
        ('--lock-wait', '5')
    ).and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={'lock_wait': 5},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--lock-wait', '5', 'repo')


def test_make_repo_list_command_includes_local_path():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
        local_path='borg2',
    )

    assert command == ('borg2', 'list', 'repo')


def test_make_repo_list_command_includes_remote_path():
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else ()
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
        remote_path='borg2',
    )

    assert command == ('borg', 'list', '--remote-path', 'borg2', 'repo')


def test_make_repo_list_command_includes_umask():
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else ()
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={'umask': '077'},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--umask', '077', 'repo')


def test_make_repo_list_command_transforms_prefix_into_match_archives():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(()).and_return(
        ('--match-archives', 'sh:foo*')
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(archive=None, paths=None, json=False, prefix='foo'),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--match-archives', 'sh:foo*', 'repo')


def test_make_repo_list_command_prefers_prefix_over_archive_name_format():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(()).and_return(
        ('--match-archives', 'sh:foo*')
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').never()
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(archive=None, paths=None, json=False, prefix='foo'),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--match-archives', 'sh:foo*', 'repo')


def test_make_repo_list_command_transforms_archive_name_format_into_match_archives():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '1.2.3'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--match-archives', 'sh:bar-*', 'repo')


def test_make_repo_list_command_includes_short():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--short',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None, paths=None, json=False, prefix=None, match_archives=None, short=True
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--short', 'repo')


@pytest.mark.parametrize(
    'argument_name',
    (
        'sort_by',
        'first',
        'last',
        'exclude',
        'exclude_from',
        'pattern',
        'patterns_from',
    ),
)
def test_make_repo_list_command_includes_additional_flags(argument_name):
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        (f"--{argument_name.replace('_', '-')}", 'value')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None,
            paths=None,
            json=False,
            prefix=None,
            match_archives=None,
            find_paths=None,
            format=None,
            **{argument_name: 'value'},
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--' + argument_name.replace('_', '-'), 'value', 'repo')


def test_make_repo_list_command_with_match_archives_calls_borg_with_match_archives_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'foo-*',
        None,
        '1.2.3',
    ).and_return(('--match-archives', 'foo-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={'match_archives': 'foo-*'},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None,
            paths=None,
            json=False,
            prefix=None,
            match_archives='foo-*',
            find_paths=None,
            format=None,
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--match-archives', 'foo-*', 'repo')


def test_list_repository_calls_two_commands():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('make_repo_list_command')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').once()
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').once()

    module.list_repository(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=argparse.Namespace(json=False),
        global_arguments=flexmock(),
    )


def test_list_repository_with_json_calls_json_command_only():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('make_repo_list_command')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    json_output = flexmock()
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(json_output)
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags').never()
    flexmock(module).should_receive('execute_command').never()

    assert (
        module.list_repository(
            repository_path='repo',
            config={},
            local_borg_version='1.2.3',
            repo_list_arguments=argparse.Namespace(json=True),
            global_arguments=flexmock(),
        )
        == json_output
    )


def test_make_repo_list_command_with_date_based_matching_calls_borg_with_date_based_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '1.2.3'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        ('--newer', '1d', '--newest', '1y', '--older', '1m', '--oldest', '1w')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_repo_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=flexmock(
            archive=None,
            paths=None,
            json=False,
            prefix=None,
            match_archives=None,
            newer='1d',
            newest='1y',
            older='1m',
            oldest='1w',
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == (
        'borg',
        'list',
        '--newer',
        '1d',
        '--newest',
        '1y',
        '--older',
        '1m',
        '--oldest',
        '1w',
        'repo',
    )


def test_list_repository_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('make_repo_list_command')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        full_command=object,
        environment=object,
        working_directory='/working/dir',
        borg_local_path=object,
        borg_exit_codes=object,
    ).once()
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').with_args(
        full_command=object,
        output_log_level=object,
        environment=object,
        working_directory='/working/dir',
        borg_local_path=object,
        borg_exit_codes=object,
    ).once()

    module.list_repository(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        repo_list_arguments=argparse.Namespace(json=False),
        global_arguments=flexmock(),
    )
