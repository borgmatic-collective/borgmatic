import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import info as module

from ..test_verbosity import insert_logging_mock


def test_display_archives_info_calls_borg_with_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--info', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )
    insert_logging_mock(logging.INFO)
    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'info', '--json', '--repo', 'repo'),
        extra_environment=None,
    ).and_return('[]')

    insert_logging_mock(logging.INFO)
    json_output = module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
    )

    assert json_output == '[]'


def test_display_archives_info_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--debug', '--show-rc', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )
    insert_logging_mock(logging.DEBUG)

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'info', '--json', '--repo', 'repo'),
        extra_environment=None,
    ).and_return('[]')

    insert_logging_mock(logging.DEBUG)
    json_output = module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
    )

    assert json_output == '[]'


def test_display_archives_info_with_json_calls_borg_with_json_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'info', '--json', '--repo', 'repo'),
        extra_environment=None,
    ).and_return('[]')

    json_output = module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=True, prefix=None, match_archives=None),
    )

    assert json_output == '[]'


def test_display_archives_info_with_archive_calls_borg_with_match_archives_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'archive', None, '2.3.4'
    ).and_return(('--match-archives', 'archive'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--match-archives', 'archive', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive='archive', json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_with_local_path_calls_borg_via_local_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1', 'info', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg1',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        local_path='borg1',
    )


def test_display_archives_info_with_remote_path_calls_borg_with_remote_path_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'remote-path', 'borg1'
    ).and_return(('--remote-path', 'borg1'))
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--remote-path', 'borg1', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
        remote_path='borg1',
    )


def test_display_archives_info_with_log_json_calls_borg_with_log_json_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('log-json', True).and_return(
        ('--log-json',)
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--log-json', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=True),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_with_lock_wait_calls_borg_with_lock_wait_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args('lock-wait', 5).and_return(
        ('--lock-wait', '5')
    )
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    storage_config = {'lock_wait': 5}
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--lock-wait', '5', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config=storage_config,
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_info_transforms_prefix_into_match_archives_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'match-archives', 'sh:foo*'
    ).and_return(('--match-archives', 'sh:foo*'))
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--match-archives', 'sh:foo*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix='foo'),
    )


def test_display_archives_info_prefers_prefix_over_archive_name_format():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'match-archives', 'sh:foo*'
    ).and_return(('--match-archives', 'sh:foo*'))
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--match-archives', 'sh:foo*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix='foo'),
    )


def test_display_archives_info_transforms_archive_name_format_into_match_archives_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--match-archives', 'sh:bar-*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_with_match_archives_option_calls_borg_with_match_archives_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'sh:foo-*', 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:foo-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--match-archives', 'sh:foo-*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={
            'archive_name_format': 'bar-{now}',  # noqa: FS003
            'match_archives': 'sh:foo-*',
        },
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives=None),
    )


def test_display_archives_with_match_archives_flag_calls_borg_with_match_archives_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        'sh:foo-*', 'bar-{now}', '2.3.4'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:foo-*'))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', '--match-archives', 'sh:foo-*', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={'archive_name_format': 'bar-{now}'},  # noqa: FS003
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(archive=None, json=False, prefix=None, match_archives='sh:foo-*'),
    )


@pytest.mark.parametrize('argument_name', ('sort_by', 'first', 'last'))
def test_display_archives_info_passes_through_arguments_to_borg(argument_name):
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
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
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'info', flag_name, 'value', '--repo', 'repo'),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )

    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=flexmock(
            archive=None, json=False, prefix=None, match_archives=None, **{argument_name: 'value'}
        ),
    )


def test_display_archives_info_with_date_based_matching_calls_borg_with_date_based_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, None, '2.3.4'
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        ('--newer', '1d', '--newest', '1y', '--older', '1m', '--oldest', '1w')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('--repo', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        (
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
        ),
        output_log_level=module.borgmatic.logger.ANSWER,
        borg_local_path='borg',
        extra_environment=None,
    )
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
    module.display_archives_info(
        repository_path='repo',
        storage_config={},
        local_borg_version='2.3.4',
        global_arguments=flexmock(log_json=False),
        info_arguments=info_arguments,
    )
