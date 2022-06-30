import argparse
import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import list as module

from ..test_verbosity import insert_logging_mock

BORG_LIST_LATEST_ARGUMENTS = (
    '--last',
    '1',
    '--short',
    'repo',
)


def test_resolve_archive_name_passes_through_non_latest_archive_name():
    archive = 'myhost-2030-01-01T14:41:17.647620'

    assert module.resolve_archive_name('repo', archive, storage_config={}) == archive


def test_resolve_archive_name_calls_borg_with_parameters():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert module.resolve_archive_name('repo', 'latest', storage_config={}) == expected_archive


def test_resolve_archive_name_with_log_info_calls_borg_with_info_parameter():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--info') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return(expected_archive + '\n')
    insert_logging_mock(logging.INFO)

    assert module.resolve_archive_name('repo', 'latest', storage_config={}) == expected_archive


def test_resolve_archive_name_with_log_debug_calls_borg_with_debug_parameter():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--debug', '--show-rc') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return(expected_archive + '\n')
    insert_logging_mock(logging.DEBUG)

    assert module.resolve_archive_name('repo', 'latest', storage_config={}) == expected_archive


def test_resolve_archive_name_with_local_path_calls_borg_via_local_path():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg1', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg1',
        extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name('repo', 'latest', storage_config={}, local_path='borg1')
        == expected_archive
    )


def test_resolve_archive_name_with_remote_path_calls_borg_with_remote_path_parameters():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--remote-path', 'borg1') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name('repo', 'latest', storage_config={}, remote_path='borg1')
        == expected_archive
    )


def test_resolve_archive_name_without_archives_raises():
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return('')

    with pytest.raises(ValueError):
        module.resolve_archive_name('repo', 'latest', storage_config={})


def test_resolve_archive_name_with_lock_wait_calls_borg_with_lock_wait_parameters():
    expected_archive = 'archive-name'

    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', '--lock-wait', 'okay') + BORG_LIST_LATEST_ARGUMENTS,
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name('repo', 'latest', storage_config={'lock_wait': 'okay'})
        == expected_archive
    )


def test_make_list_command_includes_log_info():
    insert_logging_mock(logging.INFO)

    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=False),
    )

    assert command == ('borg', 'list', '--info', 'repo')


def test_make_list_command_includes_json_but_not_info():
    insert_logging_mock(logging.INFO)

    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=True),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_list_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)

    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=False),
    )

    assert command == ('borg', 'list', '--debug', '--show-rc', 'repo')


def test_make_list_command_includes_json_but_not_debug():
    insert_logging_mock(logging.DEBUG)

    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=True),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_list_command_includes_json():
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=True),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_list_command_includes_lock_wait():
    command = module.make_list_command(
        repository='repo',
        storage_config={'lock_wait': 5},
        list_arguments=flexmock(archive=None, paths=None, json=False),
    )

    assert command == ('borg', 'list', '--lock-wait', '5', 'repo')


def test_make_list_command_includes_archive():
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive='archive', paths=None, json=False),
    )

    assert command == ('borg', 'list', 'repo::archive')


def test_make_list_command_includes_archive_and_path():
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive='archive', paths=['var/lib'], json=False),
    )

    assert command == ('borg', 'list', 'repo::archive', 'var/lib')


def test_make_list_command_includes_local_path():
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=False),
        local_path='borg2',
    )

    assert command == ('borg2', 'list', 'repo')


def test_make_list_command_includes_remote_path():
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=False),
        remote_path='borg2',
    )

    assert command == ('borg', 'list', '--remote-path', 'borg2', 'repo')


def test_make_list_command_includes_short():
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(archive=None, paths=None, json=False, short=True),
    )

    assert command == ('borg', 'list', '--short', 'repo')


@pytest.mark.parametrize(
    'argument_name',
    (
        'prefix',
        'glob_archives',
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
    command = module.make_list_command(
        repository='repo',
        storage_config={},
        list_arguments=flexmock(
            archive=None,
            paths=None,
            json=False,
            find_paths=None,
            format=None,
            **{argument_name: 'value'}
        ),
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


def test_list_archives_calls_borg_with_parameters():
    list_arguments = argparse.Namespace(archive=None, paths=None, json=False, find_paths=None)

    flexmock(module).should_receive('make_list_command').with_args(
        repository='repo',
        storage_config={},
        list_arguments=list_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
        extra_environment=None,
    ).once()

    module.list_archives(
        repository='repo', storage_config={}, list_arguments=list_arguments,
    )


def test_list_archives_with_json_suppresses_most_borg_output():
    list_arguments = argparse.Namespace(archive=None, paths=None, json=True, find_paths=None)

    flexmock(module).should_receive('make_list_command').with_args(
        repository='repo',
        storage_config={},
        list_arguments=list_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo'),
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).once()

    module.list_archives(
        repository='repo', storage_config={}, list_arguments=list_arguments,
    )


def test_list_archives_calls_borg_with_local_path():
    list_arguments = argparse.Namespace(archive=None, paths=None, json=False, find_paths=None)

    flexmock(module).should_receive('make_list_command').with_args(
        repository='repo',
        storage_config={},
        list_arguments=list_arguments,
        local_path='borg2',
        remote_path=None,
    ).and_return(('borg2', 'list', 'repo'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg2', 'list', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg2',
        extra_environment=None,
    ).once()

    module.list_archives(
        repository='repo', storage_config={}, list_arguments=list_arguments, local_path='borg2',
    )


def test_list_archives_calls_borg_multiple_times_with_find_paths():
    glob_paths = ('**/*foo.txt*/**',)
    list_arguments = argparse.Namespace(
        archive=None, paths=None, json=False, find_paths=['foo.txt'], format=None
    )

    flexmock(module).should_receive('make_list_command').and_return(
        ('borg', 'list', 'repo')
    ).and_return(('borg', 'list', 'repo::archive1')).and_return(('borg', 'list', 'repo::archive2'))
    flexmock(module).should_receive('make_find_paths').and_return(glob_paths)
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo'),
        output_log_level=None,
        borg_local_path='borg',
        extra_environment=None,
    ).and_return(
        'archive1   Sun, 2022-05-29 15:27:04 [abc]\narchive2   Mon, 2022-05-30 19:47:15 [xyz]'
    ).once()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive1') + glob_paths,
        output_log_level=logging.WARNING,
        borg_local_path='borg',
        extra_environment=None,
    ).once()
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive2') + glob_paths,
        output_log_level=logging.WARNING,
        borg_local_path='borg',
        extra_environment=None,
    ).once()

    module.list_archives(
        repository='repo', storage_config={}, list_arguments=list_arguments,
    )


def test_list_archives_calls_borg_with_archive():
    list_arguments = argparse.Namespace(archive='archive', paths=None, json=False, find_paths=None)

    flexmock(module).should_receive('make_list_command').with_args(
        repository='repo',
        storage_config={},
        list_arguments=list_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'list', 'repo::archive'))
    flexmock(module).should_receive('make_find_paths').and_return(())
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'list', 'repo::archive'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
        extra_environment=None,
    ).once()

    module.list_archives(
        repository='repo', storage_config={}, list_arguments=list_arguments,
    )
