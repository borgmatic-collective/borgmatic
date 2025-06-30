import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import check as module

from ..test_verbosity import insert_logging_mock


def insert_execute_command_mock(
    command, output_file=None, working_directory=None, borg_exit_codes=None
):
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        working_directory,
    )
    flexmock(module).should_receive('execute_command').with_args(
        command,
        output_file=output_file,
        environment=None,
        working_directory=working_directory,
        borg_local_path=command[0],
        borg_exit_codes=borg_exit_codes,
    ).once()


def insert_execute_command_never():
    flexmock(module).should_receive('execute_command').never()


def test_make_archive_filter_flags_with_default_checks_and_prefix_returns_default_flags():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo'},
        ('repository', 'archives'),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--match-archives', 'sh:foo*')


def test_make_archive_filter_flags_with_all_checks_and_prefix_returns_default_flags():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo'},
        ('repository', 'archives', 'extract'),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--match-archives', 'sh:foo*')


def test_make_archive_filter_flags_with_all_checks_and_prefix_without_borg_features_returns_glob_archives_flags():
    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo'},
        ('repository', 'archives', 'extract'),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--glob-archives', 'foo*')


def test_make_archive_filter_flags_with_archives_check_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'check_last': 3},
        ('archives',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--last', '3')


def test_make_archive_filter_flags_with_data_check_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'check_last': 3},
        ('data',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--last', '3')


def test_make_archive_filter_flags_with_repository_check_and_last_omits_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'check_last': 3},
        ('repository',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ()


def test_make_archive_filter_flags_with_default_checks_and_last_includes_last_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'check_last': 3},
        ('repository', 'archives'),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--last', '3')


def test_make_archive_filter_flags_with_archives_check_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo-'},
        ('archives',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--match-archives', 'sh:foo-*')


def test_make_archive_filter_flags_with_data_check_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo-'},
        ('data',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--match-archives', 'sh:foo-*')


def test_make_archive_filter_flags_with_archives_check_and_empty_prefix_uses_archive_name_format_instead():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').with_args(
        None, 'bar-{now}', '1.2.3'  # noqa: FS003
    ).and_return(('--match-archives', 'sh:bar-*'))

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'archive_name_format': 'bar-{now}', 'prefix': ''},  # noqa: FS003
        ('archives',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--match-archives', 'sh:bar-*')


def test_make_archive_filter_flags_with_archives_check_and_none_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {},
        ('archives',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ()


def test_make_archive_filter_flags_with_repository_check_and_prefix_omits_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo-'},
        ('repository',),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ()


def test_make_archive_filter_flags_with_default_checks_and_prefix_includes_match_archives_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_archive_filter_flags(
        '1.2.3',
        {'prefix': 'foo-'},
        ('repository', 'archives'),
        check_arguments=flexmock(match_archives=None),
    )

    assert flags == ('--match-archives', 'sh:foo-*')


def test_make_check_name_flags_with_repository_check_returns_flag():
    flags = module.make_check_name_flags({'repository'}, ())

    assert flags == ('--repository-only',)


def test_make_check_name_flags_with_archives_check_returns_flag():
    flags = module.make_check_name_flags({'archives'}, ())

    assert flags == ('--archives-only',)


def test_make_check_name_flags_with_archives_check_and_archive_filter_flags_includes_those_flags():
    flags = module.make_check_name_flags({'archives'}, ('--match-archives', 'sh:foo-*'))

    assert flags == ('--archives-only', '--match-archives', 'sh:foo-*')


def test_make_check_name_flags_without_archives_check_and_with_archive_filter_flags_includes_those_flags():
    flags = module.make_check_name_flags({'repository'}, ('--match-archives', 'sh:foo-*'))

    assert flags == ('--repository-only',)


def test_make_check_name_flags_with_archives_and_data_check_returns_verify_data_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_check_name_flags({'archives', 'data'}, ())

    assert flags == (
        '--archives-only',
        '--verify-data',
    )


def test_make_check_name_flags_with_repository_and_data_check_returns_verify_data_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_check_name_flags({'archives', 'data', 'repository'}, ())

    assert flags == ('--verify-data',)


def test_make_check_name_flags_with_extract_omits_extract_flag():
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.flags).should_receive('make_match_archives_flags').and_return(())

    flags = module.make_check_name_flags({'extract'}, ())

    assert flags == ()


def test_get_repository_id_with_valid_json_does_not_raise():
    config = {}
    flexmock(module.repo_info).should_receive('display_repository_info').and_return(
        '{"repository": {"id": "repo"}}'
    )

    assert module.get_repository_id(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        global_arguments=flexmock(),
        local_path='borg',
        remote_path=None,
    )


def test_get_repository_id_with_json_error_raises():
    config = {}
    flexmock(module.repo_info).should_receive('display_repository_info').and_return(
        '{"unexpected": {"id": "repo"}}'
    )

    with pytest.raises(ValueError):
        module.get_repository_id(
            repository_path='repo',
            config=config,
            local_borg_version='1.2.3',
            global_arguments=flexmock(),
            local_path='borg',
            remote_path=None,
        )


def test_get_repository_id_with_missing_json_keys_raises():
    config = {}
    flexmock(module.repo_info).should_receive('display_repository_info').and_return('{invalid JSON')

    with pytest.raises(ValueError):
        module.get_repository_id(
            repository_path='repo',
            config=config,
            local_borg_version='1.2.3',
            global_arguments=flexmock(),
            local_path='borg',
            remote_path=None,
        )


def test_check_archives_with_progress_passes_through_to_borg():
    config = {'progress': True}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--progress', 'repo'),
        output_file=module.DO_NOT_CAPTURE,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_repair_passes_through_to_borg():
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--repair', 'repo'),
        output_file=module.DO_NOT_CAPTURE,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=True,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_flag_passes_through_to_borg():
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--max-duration', '33', 'repo'),
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=33,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_option_passes_through_to_borg():
    config = {'checks': [{'name': 'repository', 'max_duration': 33}]}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--max-duration', '33', 'repo'),
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_option_and_archives_check_runs_repository_check_separately():
    config = {'checks': [{'name': 'repository', 'max_duration': 33}, {'name': 'archives'}]}
    flexmock(module).should_receive('make_check_name_flags').with_args({'archives'}, ()).and_return(
        ('--archives-only',)
    )
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(('--repository-only',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--archives-only', 'repo'))
    insert_execute_command_mock(
        ('borg', 'check', '--max-duration', '33', '--repository-only', 'repo')
    )

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository', 'archives'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_flag_and_archives_check_runs_repository_check_separately():
    config = {'checks': [{'name': 'repository'}, {'name': 'archives'}]}
    flexmock(module).should_receive('make_check_name_flags').with_args({'archives'}, ()).and_return(
        ('--archives-only',)
    )
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(('--repository-only',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--archives-only', 'repo'))
    insert_execute_command_mock(
        ('borg', 'check', '--max-duration', '33', '--repository-only', 'repo')
    )

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=33,
        ),
        global_arguments=flexmock(),
        checks={'repository', 'archives'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_option_and_data_check_runs_repository_check_separately():
    config = {'checks': [{'name': 'repository', 'max_duration': 33}, {'name': 'data'}]}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'data', 'archives'}, ()
    ).and_return(('--archives-only', '--verify-data'))
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(('--repository-only',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--archives-only', '--verify-data', 'repo'))
    insert_execute_command_mock(
        ('borg', 'check', '--max-duration', '33', '--repository-only', 'repo')
    )

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository', 'data'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_flag_and_data_check_runs_repository_check_separately():
    config = {'checks': [{'name': 'repository'}, {'name': 'data'}]}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'data', 'archives'}, ()
    ).and_return(('--archives-only', '--verify-data'))
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(('--repository-only',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--archives-only', '--verify-data', 'repo'))
    insert_execute_command_mock(
        ('borg', 'check', '--max-duration', '33', '--repository-only', 'repo')
    )

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=33,
        ),
        global_arguments=flexmock(),
        checks={'repository', 'data'},
        archive_filter_flags=(),
    )


def test_check_archives_with_max_duration_flag_overrides_max_duration_option():
    config = {'checks': [{'name': 'repository', 'max_duration': 33}]}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--max-duration', '44', 'repo'),
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=44,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


@pytest.mark.parametrize(
    'checks',
    (
        ('repository',),
        ('archives',),
        ('repository', 'archives'),
        ('repository', 'archives', 'other'),
    ),
)
def test_check_archives_calls_borg_with_parameters(checks):
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
    )


def test_check_archives_with_data_check_implies_archives_check_calls_borg_with_parameters():
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'data', 'archives'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'data'},
        archive_filter_flags=(),
    )


def test_check_archives_with_log_info_passes_through_to_borg():
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_logging_mock(logging.INFO)
    insert_execute_command_mock(('borg', 'check', '--info', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_log_debug_passes_through_to_borg():
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_logging_mock(logging.DEBUG)
    insert_execute_command_mock(('borg', 'check', '--debug', '--show-rc', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_local_path_calls_borg_via_local_path():
    checks = {'repository'}
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg1', 'check', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
        local_path='borg1',
    )


def test_check_archives_with_exit_codes_calls_borg_using_them():
    checks = {'repository'}
    borg_exit_codes = flexmock()
    config = {'borg_exit_codes': borg_exit_codes}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'), borg_exit_codes=borg_exit_codes)

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
    )


def test_check_archives_with_remote_path_passes_through_to_borg():
    checks = {'repository'}
    config = {}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--remote-path', 'borg1', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
        remote_path='borg1',
    )


def test_check_archives_with_umask_passes_through_to_borg():
    checks = {'repository'}
    config = {'umask': '077'}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--umask', '077', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
    )


def test_check_archives_with_log_json_passes_through_to_borg():
    checks = {'repository'}
    config = {'log_json': True}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--log-json', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
    )


def test_check_archives_with_lock_wait_passes_through_to_borg():
    checks = {'repository'}
    config = {'lock_wait': 5}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', '--lock-wait', '5', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
    )


def test_check_archives_with_retention_prefix():
    checks = {'repository'}
    prefix = 'foo-'
    config = {'prefix': prefix}
    flexmock(module).should_receive('make_check_name_flags').with_args(checks, ()).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(('borg', 'check', 'repo'))

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks=checks,
        archive_filter_flags=(),
    )


def test_check_archives_with_extra_borg_options_passes_through_to_borg():
    config = {'extra_borg_options': {'check': '--extra --options "value with space"'}}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    insert_execute_command_mock(
        ('borg', 'check', '--extra', '--options', 'value with space', 'repo')
    )

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )


def test_check_archives_with_match_archives_passes_through_to_borg():
    config = {'checks': [{'name': 'archives'}]}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'archives'}, object
    ).and_return(('--match-archives', 'foo-*'))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'check', '--match-archives', 'foo-*', 'repo'),
        output_file=None,
        environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=None,
            repair=None,
            only_checks=None,
            force=None,
            match_archives='foo-*',
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'archives'},
        archive_filter_flags=('--match-archives', 'foo-*'),
    )


def test_check_archives_calls_borg_with_working_directory():
    config = {'working_directory': '/working/dir'}
    flexmock(module).should_receive('make_check_name_flags').with_args(
        {'repository'}, ()
    ).and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    insert_execute_command_mock(('borg', 'check', 'repo'), working_directory='/working/dir')

    module.check_archives(
        repository_path='repo',
        config=config,
        local_borg_version='1.2.3',
        check_arguments=flexmock(
            progress=False,
            repair=None,
            only_checks=None,
            force=None,
            match_archives=None,
            max_duration=None,
        ),
        global_arguments=flexmock(),
        checks={'repository'},
        archive_filter_flags=(),
    )
