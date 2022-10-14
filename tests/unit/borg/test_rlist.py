import argparse
import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import rlist as module

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
        module.resolve_archive_name('repo', archive, storage_config={}, local_borg_version='1.2.3')
        == archive
    )


def test_resolve_archive_name_calls_borg_with_parameters():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS, extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name('repo', 'latest', storage_config={}, local_borg_version='1.2.3')
        == expected_archive
    )


def test_resolve_archive_name_with_log_info_calls_borg_without_info_parameter():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS, extra_environment=None,
    ).and_return(expected_archive + '\n')
    insert_logging_mock(logging.INFO)

    assert (
        module.resolve_archive_name('repo', 'latest', storage_config={}, local_borg_version='1.2.3')
        == expected_archive
    )


def test_resolve_archive_name_with_log_debug_calls_borg_without_debug_parameter():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS, extra_environment=None,
    ).and_return(expected_archive + '\n')
    insert_logging_mock(logging.DEBUG)

    assert (
        module.resolve_archive_name('repo', 'latest', storage_config={}, local_borg_version='1.2.3')
        == expected_archive
    )


def test_resolve_archive_name_with_local_path_calls_borg_via_local_path():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg1', 'list') + BORG_LIST_LATEST_ARGUMENTS, extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo', 'latest', storage_config={}, local_borg_version='1.2.3', local_path='borg1'
        )
        == expected_archive
    )


def test_resolve_archive_name_with_remote_path_calls_borg_with_remote_path_parameters():
    expected_archive = 'archive-name'
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', '--remote-path', 'borg1') + BORG_LIST_LATEST_ARGUMENTS,
        extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo', 'latest', storage_config={}, local_borg_version='1.2.3', remote_path='borg1'
        )
        == expected_archive
    )


def test_resolve_archive_name_without_archives_raises():
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list') + BORG_LIST_LATEST_ARGUMENTS, extra_environment=None,
    ).and_return('')

    with pytest.raises(ValueError):
        module.resolve_archive_name('repo', 'latest', storage_config={}, local_borg_version='1.2.3')


def test_resolve_archive_name_with_lock_wait_calls_borg_with_lock_wait_parameters():
    expected_archive = 'archive-name'

    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'list', '--lock-wait', 'okay') + BORG_LIST_LATEST_ARGUMENTS,
        extra_environment=None,
    ).and_return(expected_archive + '\n')

    assert (
        module.resolve_archive_name(
            'repo', 'latest', storage_config={'lock_wait': 'okay'}, local_borg_version='1.2.3'
        )
        == expected_archive
    )


def test_make_rlist_command_includes_log_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix=None),
    )

    assert command == ('borg', 'list', '--info', 'repo')


def test_make_rlist_command_includes_json_but_not_info():
    insert_logging_mock(logging.INFO)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=True, prefix=None),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_rlist_command_includes_log_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix=None),
    )

    assert command == ('borg', 'list', '--debug', '--show-rc', 'repo')


def test_make_rlist_command_includes_json_but_not_debug():
    insert_logging_mock(logging.DEBUG)
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=True, prefix=None),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_rlist_command_includes_json():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--json',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=True, prefix=None),
    )

    assert command == ('borg', 'list', '--json', 'repo')


def test_make_rlist_command_includes_lock_wait():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(
        ('--lock-wait', '5')
    ).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={'lock_wait': 5},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix=None),
    )

    assert command == ('borg', 'list', '--lock-wait', '5', 'repo')


def test_make_rlist_command_includes_local_path():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix=None),
        local_path='borg2',
    )

    assert command == ('borg2', 'list', 'repo')


def test_make_rlist_command_includes_remote_path():
    flexmock(module.flags).should_receive('make_flags').and_return(
        ('--remote-path', 'borg2')
    ).and_return(()).and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix=None),
        remote_path='borg2',
    )

    assert command == ('borg', 'list', '--remote-path', 'borg2', 'repo')


def test_make_rlist_command_transforms_prefix_into_match_archives():
    flexmock(module.flags).should_receive('make_flags').and_return(()).and_return(()).and_return(
        ('--match-archives', 'sh:foo*')
    )
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(())
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix='foo'),
    )

    assert command == ('borg', 'list', '--match-archives', 'sh:foo*', 'repo')


def test_make_rlist_command_includes_short():
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(('--short',))
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(archive=None, paths=None, json=False, prefix=None, short=True),
    )

    assert command == ('borg', 'list', '--short', 'repo')


@pytest.mark.parametrize(
    'argument_name',
    (
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
def test_make_rlist_command_includes_additional_flags(argument_name):
    flexmock(module.flags).should_receive('make_flags').and_return(())
    flexmock(module.flags).should_receive('make_flags_from_arguments').and_return(
        (f"--{argument_name.replace('_', '-')}", 'value')
    )
    flexmock(module.flags).should_receive('make_repository_flags').and_return(('repo',))

    command = module.make_rlist_command(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=flexmock(
            archive=None,
            paths=None,
            json=False,
            prefix=None,
            find_paths=None,
            format=None,
            **{argument_name: 'value'},
        ),
    )

    assert command == ('borg', 'list', '--' + argument_name.replace('_', '-'), 'value', 'repo')


def test_list_repository_calls_borg_with_parameters():
    rlist_arguments = argparse.Namespace(json=False)

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module).should_receive('make_rlist_command').with_args(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=rlist_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'rlist', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'rlist', 'repo'),
        output_log_level=logging.WARNING,
        borg_local_path='borg',
        extra_environment=None,
    ).once()

    module.list_repository(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=rlist_arguments,
    )


def test_list_repository_with_json_returns_borg_output():
    rlist_arguments = argparse.Namespace(json=True)
    json_output = flexmock()

    flexmock(module.feature).should_receive('available').and_return(False)
    flexmock(module).should_receive('make_rlist_command').with_args(
        repository='repo',
        storage_config={},
        local_borg_version='1.2.3',
        rlist_arguments=rlist_arguments,
        local_path='borg',
        remote_path=None,
    ).and_return(('borg', 'rlist', 'repo'))
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(json_output)

    assert (
        module.list_repository(
            repository='repo',
            storage_config={},
            local_borg_version='1.2.3',
            rlist_arguments=rlist_arguments,
        )
        == json_output
    )
