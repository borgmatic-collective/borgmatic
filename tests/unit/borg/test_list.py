import argparse
import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import list as module

from ..test_verbosity import insert_logging_mock


def test_make_list_command_includes_log_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--info', 'repo')


def test_make_list_command_includes_json_but_not_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=True),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_list_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--debug', '--show-rc', 'repo')


def test_make_list_command_includes_json_but_not_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=True),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_list_command_includes_json():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=True),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_list_command_includes_log_json():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(('--log-json',))
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False),
        global_arguments=flexmock(log_json=True),
    )

    assert command == ('borg', 'list', '--log-json', 'repo')


def test_make_list_command_includes_lock_wait():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(
        ('--lock-wait', '5')
    )
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={'lock_wait': 5},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--lock-wait', '5', 'repo')


def test_make_list_command_includes_archive():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive='archive', paths=None, json=False),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', 'repo::archive')


def test_make_list_command_includes_archive_and_path():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::archive',)
    )

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive='archive', paths=['var/lib'], json=False),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', 'repo::archive', 'var/lib')


def test_make_list_command_includes_local_path():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False),
        global_arguments=flexmock(log_json=False),
        local_path='borg2',
    )

    assert command == ('borg2', 'list', 'repo')


def test_make_list_command_includes_remote_path():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags').with_args(
        'remote-path', 'borg2'
    ).and_return(('--remote-path', 'borg2'))
    flexmock(module.flags).should_receive('make_flags').with_args('log-json', True).and_return(
        ('--log-json')
    )
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False),
        global_arguments=flexmock(log_json=False),
        remote_path='borg2',
    )

    assert command == ('borg', 'list', '--remote-path', 'borg2', 'repo')


def test_make_list_command_includes_short():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--short',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(archive=None, paths=None, json=False, short=True),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--short', 'repo')


@pytest.mark.parametrize(
    'argument_name',
    (
        'prefix',
        'match_archives',
        'sort_by',
        'first',
        'last',
        'exclude',
        'exclude_from',
        'pattern',
        'patterns_from',
    ),
)
def test_make_list_command_includes_additional_flags(argument_name):
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        (f"--{argument_name.replace('_', '-')}", 'value')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_list_command(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=flexmock(
            archive=None,
            paths=None,
            json=False,
            find_paths=None,
            format=None,
            **{argument_name: 'value'},
        ),
        global_arguments=flexmock(log_json=False),
    )

    assert command == ('borg', 'list', '--' + argument_name.replace('_', '-'), 'value', 'repo')


def test_make_find_paths_considers_none_as_empty_paths():
    assert module.make_find_paths(None) == ()


def test_make_find_paths_passes_through_patterns():
    find_paths = (
        'fm:*',
        'sh:**/*.txt',
        're:^.*$',
        'pp:root/somedir',
        'pf:root/foo.txt',
        'R /',
        'r /',
        'p /',
        'P /',
        '+ /',
        '- /',
        '! /',
    )

    assert module.make_find_paths(find_paths) == find_paths


def test_make_find_paths_adds_globs_to_path_fragments():
    assert module.make_find_paths(('foo.txt',)) == ('sh:**/*foo.txt*/**',)


def test_capture_archive_listing_does_not_raise():
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').and_return('')
    flexmock(module).should_receive('make_list_command')

    module.capture_archive_listing(
        repository_path='repo',
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(log_json=False),
    )


def test_list_archive_calls_borg_with_flags():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive='archive',
        paths=None,
        json=False,
        find_paths=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
    )
    global_arguments = flexmock(log_json=False)

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'),
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
    )


def test_list_archive_with_archive_and_json_errors():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(archive='archive', paths=None, json=True, find_paths=None)

    flexmock(module.feature).should_receive('available').and_return(False)

    with pytest.raises(ValueError):
        module.list_archive(
            repository_path='repo',
            config={},
            local_borg_version='1.2.3',
            list_arguments=list_arguments,
            global_arguments=flexmock(log_json=False),
        )


def test_list_archive_calls_borg_with_local_path():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive='archive',
        paths=None,
        json=False,
        find_paths=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
    )
    global_arguments = flexmock(log_json=False)

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
        local_path='borg2',
        remote_path=None,
    ).and_return(('borg2', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg2', 'list', 'repo::archive'),
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg2',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
        local_path='borg2',
    )


def test_list_archive_calls_borg_using_exit_codes():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive='archive',
        paths=None,
        json=False,
        find_paths=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
    )
    global_arguments = flexmock(log_json=False)

    flexmock(module.feature).should_receive('available').and_return(False)
    borg_exit_codes = flexmock()
    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'),
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={'borg_exit_codes': borg_exit_codes},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
    )


def test_list_archive_calls_borg_multiple_times_with_find_paths():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    glob_paths = ('**/*foo.txt*/**',)
    list_arguments = argparse.Namespace(
        archive=None,
        json=False,
        find_paths=['foo.txt'],
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
    )

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.repo_list).should_receive('make_repo_list_command').and_return(
        ('borg', 'list', 'repo')
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', 'repo'),
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return('archive1\narchive2').once()
    flexmock(module).should_receive('make_list_command').and_return(
        ('borg', 'list', 'repo::archive1')
    ).and_return(('borg', 'list', 'repo::archive2'))
    flexmock(module).should_receive('make_find_paths').and_return(glob_paths)
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive1') + glob_paths,
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive2') + glob_paths,
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=flexmock(log_json=False),
    )


def test_list_archive_calls_borg_with_archive():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive='archive',
        paths=None,
        json=False,
        find_paths=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
    )
    global_arguments = flexmock(log_json=False)

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'),
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
    )


def test_list_archive_without_archive_delegates_to_list_repository():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive=None,
        short=None,
        format=None,
        json=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
        find_paths=None,
    )

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module.repo_list).should_receive('list_repository')
    flexmock(module.environment).should_receive('make_environment').never()
    flexmock(module).should_receive('execute_command').never()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=flexmock(log_json=False),
    )


def test_list_archive_with_borg_features_without_archive_delegates_to_list_repository():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive=None,
        short=None,
        format=None,
        json=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
        find_paths=None,
    )

    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module.repo_list).should_receive('list_repository')
    flexmock(module.environment).should_receive('make_environment').never()
    flexmock(module).should_receive('execute_command').never()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=flexmock(log_json=False),
    )


@pytest.mark.parametrize(
    'archive_filter_flag',
    (
        'prefix',
        'match_archives',
        'sort_by',
        'first',
        'last',
    ),
)
def test_list_archive_with_archive_ignores_archive_filter_flag(
    archive_filter_flag,
):
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    global_arguments = flexmock(log_json=False)
    default_filter_flags = {
        'prefix': None,
        'match_archives': None,
        'sort_by': None,
        'first': None,
        'last': None,
    }
    altered_filter_flags = {**default_filter_flags, **{archive_filter_flag: 'foo'}}

    flexmock(module.feature).should_receive('available').with_args(
        module.feature.Feature.REPO_LIST, '1.2.3'
    ).and_return(False)
    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=argparse.Namespace(
            archive='archive', paths=None, json=False, find_paths=None, **default_filter_flags
        ),
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'),
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=argparse.Namespace(
            archive='archive', paths=None, json=False, find_paths=None, **altered_filter_flags
        ),
        global_arguments=global_arguments,
    )


@pytest.mark.parametrize(
    'archive_filter_flag',
    (
        'prefix',
        'match_archives',
        'sort_by',
        'first',
        'last',
    ),
)
def test_list_archive_with_find_paths_allows_archive_filter_flag_but_only_passes_it_to_repo_list(
    archive_filter_flag,
):
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    default_filter_flags = {
        'prefix': None,
        'match_archives': None,
        'sort_by': None,
        'first': None,
        'last': None,
    }
    altered_filter_flags = {**default_filter_flags, **{archive_filter_flag: 'foo'}}
    glob_paths = ('**/*foo.txt*/**',)
    global_arguments = flexmock(log_json=False)
    flexmock(module.feature).should_receive('available').and_return(True)

    flexmock(module.repo_list).should_receive('make_repo_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        repo_list_arguments=argparse.Namespace(
            repository='repo', short=True, format=None, json=None, **altered_filter_flags
        ),
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'repo-list', '--repo', 'repo'))

    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'repo-list', '--repo', 'repo'),
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return('archive1\narchive2').once()

    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=argparse.Namespace(
            repository='repo',
            archive='archive1',
            paths=None,
            short=True,
            format=None,
            json=None,
            find_paths=['foo.txt'],
            **default_filter_flags,
        ),
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', '--repo', 'repo', 'archive1'))

    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=argparse.Namespace(
            repository='repo',
            archive='archive2',
            paths=None,
            short=True,
            format=None,
            json=None,
            find_paths=['foo.txt'],
            **default_filter_flags,
        ),
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', '--repo', 'repo', 'archive2'))

    flexmock(module).should_receive('make_find_paths').and_return(glob_paths)
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--repo', 'repo', 'archive1') + glob_paths,
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--repo', 'repo', 'archive2') + glob_paths,
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={},
        local_borg_version='1.2.3',
        list_arguments=argparse.Namespace(
            repository='repo',
            archive=None,
            paths=None,
            short=True,
            format=None,
            json=None,
            find_paths=['foo.txt'],
            **altered_filter_flags,
        ),
        global_arguments=global_arguments,
    )


def test_list_archive_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module.logger).answer = lambda message: None
    list_arguments = argparse.Namespace(
        archive='archive',
        paths=None,
        json=False,
        find_paths=None,
        prefix=None,
        match_archives=None,
        sort_by=None,
        first=None,
        last=None,
    )
    global_arguments = flexmock(log_json=False)

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module).should_receive('make_list_command').with_args(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'),
        output_log_level=module.borgmatic.logger.ANSWER,
        extra_environment=None,
        working_directory='/working/dir',
        borg_local_path='borg',
        borg_exit_codes=None,
    ).once()

    module.list_archive(
        repository_path='repo',
        config={'working_directory': '/working/dir'},
        local_borg_version='1.2.3',
        list_arguments=list_arguments,
        global_arguments=global_arguments,
    )
