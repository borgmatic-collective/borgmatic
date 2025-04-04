import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import info as module

from ..test_verbosity import insert_logging_mock


def test_make_info_command_constructs_borg_info_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--repo', 'repo')


def test_make_info_command_with_log_info_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    insert_logging_mock(logging.INFO)

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--info', '--repo', 'repo')


def test_make_info_command_with_log_info_and_json_omits_borg_logging_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    insert_logging_mock(logging.INFO)

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--json', '--repo', 'repo')


def test_make_info_command_with_log_debug_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    insert_logging_mock(logging.DEBUG)

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--debug', '--show-rc', '--repo', 'repo')


def test_make_info_command_with_log_debug_and_json_omits_borg_logging_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--json', '--repo', 'repo')


def test_make_info_command_with_json_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--json', '--repo', 'repo')


def test_make_info_command_with_archive_uses_match_archives_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'archive', None, '2.3.4'
    ).and_return(('--match-archives', 'archive'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive='archive', json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--match-archives', 'archive', '--repo', 'repo')


def test_make_info_command_with_local_path_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg1',
        remote_path=None,
    )

    command == ('borg1', 'info', '--repo', 'repo')


def test_make_info_command_with_remote_path_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'remote-path', 'borg1'
    ).and_return(('--remote-path', 'borg1'))
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path='borg1',
    )

    assert command == ('borg', 'info', '--remote-path', 'borg1', '--repo', 'repo')


def test_make_info_command_with_umask_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').replace_with(
        lambda name, value: (f'--{name}', value) if value else ()
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={'umask': '077'},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--umask', '077', '--repo', 'repo')


def test_make_info_command_with_log_json_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('log-json', True).and_return(
        ('--log-json',)
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={'log_json': True},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--log-json', '--repo', 'repo')


def test_make_info_command_with_lock_wait_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('lock-wait', 5).and_return(
        ('--lock-wait', '5')
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    config = {'lock_wait': 5}

    command = module.make_info_command(
        repository_path='repo',
        config=config,
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--lock-wait', '5', '--repo', 'repo')


def test_make_info_command_transforms_prefix_into_match_archives_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'match-archives', 'sh:foo*'
    ).and_return(('--match-archives', 'sh:foo*'))
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix='foo'),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--match-archives', 'sh:foo*', '--repo', 'repo')


def test_make_info_command_prefers_prefix_over_archive_name_format():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'match-archives', 'sh:foo*'
    ).and_return(('--match-archives', 'sh:foo*'))
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix='foo'),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--match-archives', 'sh:foo*', '--repo', 'repo')


def test_make_info_command_transforms_archive_name_format_into_match_archives_flags():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))

    command = module.make_info_command(
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--match-archives', 'sh:bar-*', '--repo', 'repo')


def test_make_info_command_with_match_archives_option_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'sh:foo-*', 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:foo-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')

    command = module.make_info_command(
        repository_path='repo',
        config={
            'archive_name_format': 'bar-{now}',  # noqa: FS003
            'match_archives': 'sh:foo-*',
        },
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--match-archives', 'sh:foo-*', '--repo', 'repo')


def test_make_info_command_with_match_archives_flag_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'sh:foo-*', 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:foo-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')

    command = module.make_info_command(
        repository_path='repo',
        config={'archive_name_format': 'bar-{now}', 'match_archives': 'sh:foo-*'},  # noqa: FS003
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives='sh:foo-*'),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', '--match-archives', 'sh:foo-*', '--repo', 'repo')


@pytest.mark.parametrize('argument_name', ('sort_by', 'first', 'last'))
def test_make_info_command_passes_arguments_through_to_command(argument_name):
    flag_name = f"--{argument_name.replace('_', ' ')}"
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        (flag_name, 'value')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(
            archive=None, json=False, prefix=None, match_archives=None, **{argument_name: 'value'}
        ),
        local_path='borg',
        remote_path=None,
    )

    assert command == ('borg', 'info', flag_name, 'value', '--repo', 'repo')


def test_make_info_command_with_date_based_matching_passes_through_to_command():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        ('--newer', '1d', '--newest', '1y', '--older', '1m', '--oldest', '1w')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    info_arguments = flexmock(
        archive=None,
        json=False,
        prefix=None,
        match_archives=None,
        newer='1d',
        newest='1y',
        older='1m',
        oldest='1w',
    )

    command = module.make_info_command(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=info_arguments,
        local_path='borg',
        remote_path=None,
    )

    assert command == (
        'borg',
        'info',
        '--newer',
        '1d',
        '--newest',
        '1y',
        '--older',
        '1m',
        '--oldest',
        '1w',
        '--repo',
        'repo',
    )


def test_display_archives_info_calls_two_commands():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('make_info_command')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').once()
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags')
    flexmock(module).should_receive('execute_command').once()

    module.display_archives_info(
        repository_path='repo',
        config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_with_json_calls_json_command_only():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('make_info_command')
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    json_output = flexmock()
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(json_output)
    flexmock(module.flags).should_receive('warn_for_aggressive_archive_flags').never()
    flexmock(module).should_receive('execute_command').never()

    assert (
        module.display_archives_info(
            repository_path='repo',
            config={},
            local_borg_version='2.3.4',
            global_arguments=flexmock(),
            info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
        )
        == json_output
    )


def test_display_archives_info_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module).should_receive('make_info_command')
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

    module.display_archives_info(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='2.3.4',
        global_arguments=flexmock(),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )
