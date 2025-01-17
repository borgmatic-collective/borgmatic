import logging

import pytest
from flexmock import flexmock

from borgmatic.borg import create as module
from borgmatic.borg.pattern import Pattern, Pattern_style, Pattern_type

from ..test_verbosity import insert_logging_mock


def test_write_patterns_file_writes_pattern_lines():
    temporary_file = flexmock(name='filename', flush=lambda: None)
    temporary_file.should_receive('write').with_args('R /foo\n+ sh:/foo/bar')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').and_return(temporary_file)

    module.write_patterns_file(
        [Pattern('/foo'), Pattern('/foo/bar', Pattern_type.INCLUDE, Pattern_style.SHELL)],
        borgmatic_runtime_directory='/run/user/0',
        log_prefix='test.yaml',
    )


def test_write_patterns_file_with_empty_exclude_patterns_does_not_raise():
    module.write_patterns_file(
        [], borgmatic_runtime_directory='/run/user/0', log_prefix='test.yaml'
    )


def test_write_patterns_file_appends_to_existing():
    patterns_file = flexmock(name='filename', flush=lambda: None)
    patterns_file.should_receive('write').with_args('\n')
    patterns_file.should_receive('write').with_args('R /foo\n+ /foo/bar')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').never()

    module.write_patterns_file(
        [Pattern('/foo'), Pattern('/foo/bar', Pattern_type.INCLUDE)],
        borgmatic_runtime_directory='/run/user/0',
        log_prefix='test.yaml',
        patterns_file=patterns_file,
    )


def test_make_exclude_flags_includes_exclude_caches_when_true_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_caches': True})

    assert exclude_flags == ('--exclude-caches',)


def test_make_exclude_flags_does_not_include_exclude_caches_when_false_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_caches': False})

    assert exclude_flags == ()


def test_make_exclude_flags_includes_exclude_if_present_when_in_config():
    exclude_flags = module.make_exclude_flags(
        config={'exclude_if_present': ['exclude_me', 'also_me']}
    )

    assert exclude_flags == (
        '--exclude-if-present',
        'exclude_me',
        '--exclude-if-present',
        'also_me',
    )


def test_make_exclude_flags_includes_keep_exclude_tags_when_true_in_config():
    exclude_flags = module.make_exclude_flags(config={'keep_exclude_tags': True})

    assert exclude_flags == ('--keep-exclude-tags',)


def test_make_exclude_flags_does_not_include_keep_exclude_tags_when_false_in_config():
    exclude_flags = module.make_exclude_flags(config={'keep_exclude_tags': False})

    assert exclude_flags == ()


def test_make_exclude_flags_includes_exclude_nodump_when_true_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_nodump': True})

    assert exclude_flags == ('--exclude-nodump',)


def test_make_exclude_flags_does_not_include_exclude_nodump_when_false_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_nodump': False})

    assert exclude_flags == ()


def test_make_exclude_flags_is_empty_when_config_has_no_excludes():
    exclude_flags = module.make_exclude_flags(config={})

    assert exclude_flags == ()


def test_make_list_filter_flags_with_debug_and_feature_available_includes_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(True)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AME+-'


def test_make_list_filter_flags_with_info_and_feature_available_omits_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(False)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AME'


def test_make_list_filter_flags_with_debug_and_feature_available_and_dry_run_includes_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(True)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=True) == 'AME+-'


def test_make_list_filter_flags_with_info_and_feature_available_and_dry_run_includes_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(False)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=True) == 'AME+-'


def test_make_list_filter_flags_with_debug_and_feature_not_available_includes_x():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(True)
    flexmock(module.feature).should_receive('available').and_return(False)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AMEx-'


def test_make_list_filter_flags_with_info_and_feature_not_available_omits_x():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(False)
    flexmock(module.feature).should_receive('available').and_return(False)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AME-'


@pytest.mark.parametrize(
    'character_device,block_device,fifo,expected_result',
    (
        (False, False, False, False),
        (True, False, False, True),
        (False, True, False, True),
        (True, True, False, True),
        (False, False, True, True),
        (False, True, True, True),
        (True, False, True, True),
    ),
)
def test_special_file_looks_at_file_type(character_device, block_device, fifo, expected_result):
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_mode=flexmock()))
    flexmock(module.stat).should_receive('S_ISCHR').and_return(character_device)
    flexmock(module.stat).should_receive('S_ISBLK').and_return(block_device)
    flexmock(module.stat).should_receive('S_ISFIFO').and_return(fifo)

    assert module.special_file('/dev/special') == expected_result


def test_special_file_treats_broken_symlink_as_non_special():
    flexmock(module.os).should_receive('stat').and_raise(FileNotFoundError)

    assert module.special_file('/broken/symlink') is False


def test_special_file_prepends_relative_path_with_working_directory():
    flexmock(module.os).should_receive('stat').with_args('/working/dir/relative').and_return(
        flexmock(st_mode=flexmock())
    )
    flexmock(module.stat).should_receive('S_ISCHR').and_return(False)
    flexmock(module.stat).should_receive('S_ISBLK').and_return(False)
    flexmock(module.stat).should_receive('S_ISFIFO').and_return(False)

    assert module.special_file('relative', '/working/dir') is False


def test_any_parent_directories_treats_parents_as_match():
    module.any_parent_directories('/foo/bar.txt', ('/foo', '/etc'))


def test_any_parent_directories_treats_grandparents_as_match():
    module.any_parent_directories('/foo/bar/baz.txt', ('/foo', '/etc'))


def test_any_parent_directories_treats_unrelated_paths_as_non_match():
    module.any_parent_directories('/foo/bar.txt', ('/usr', '/etc'))


def test_collect_special_file_paths_parses_special_files_from_borg_dry_run_file_list():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        'Processing files ...\n- /foo\n+ /bar\n- /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True)
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('any_parent_directories').never()

    assert module.collect_special_file_paths(
        dry_run=False,
        create_command=('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/foo', '/bar', '/baz')


def test_collect_special_file_paths_skips_borgmatic_runtime_directory():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '+ /foo\n- /run/borgmatic/bar\n- /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('any_parent_directories').with_args(
        '/foo', ('/run/borgmatic',)
    ).and_return(False)
    flexmock(module).should_receive('any_parent_directories').with_args(
        '/run/borgmatic/bar', ('/run/borgmatic',)
    ).and_return(True)
    flexmock(module).should_receive('any_parent_directories').with_args(
        '/baz', ('/run/borgmatic',)
    ).and_return(False)

    assert module.collect_special_file_paths(
        dry_run=False,
        create_command=('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/foo', '/baz')


def test_collect_special_file_paths_with_borgmatic_runtime_directory_missing_from_paths_output_errors():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '+ /foo\n- /bar\n- /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('any_parent_directories').and_return(False)

    with pytest.raises(ValueError):
        module.collect_special_file_paths(
            dry_run=False,
            create_command=('borg', 'create'),
            config={},
            local_path=None,
            working_directory=None,
            borg_environment=None,
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_collect_special_file_paths_with_dry_run_and_borgmatic_runtime_directory_missing_from_paths_output_does_not_raise():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '+ /foo\n- /bar\n- /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True)
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('any_parent_directories').and_return(False)

    assert module.collect_special_file_paths(
        dry_run=True,
        create_command=('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/foo', '/bar', '/baz')


def test_collect_special_file_paths_excludes_non_special_files():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '+ /foo\n+ /bar\n+ /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True).and_return(False).and_return(
        True
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('any_parent_directories').never()

    assert module.collect_special_file_paths(
        dry_run=False,
        create_command=('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/foo', '/baz')


def test_collect_special_file_paths_omits_exclude_no_dump_flag_from_command():
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--dry-run', '--list'),
        capture_stderr=True,
        working_directory=None,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return('Processing files ...\n- /foo\n+ /bar\n- /baz').once()
    flexmock(module).should_receive('special_file').and_return(True)
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('any_parent_directories').never()

    module.collect_special_file_paths(
        dry_run=False,
        create_command=('borg', 'create', '--exclude-nodump'),
        config={},
        local_path='borg',
        working_directory=None,
        borg_environment=None,
        borgmatic_runtime_directory='/run/borgmatic',
    )


DEFAULT_ARCHIVE_NAME = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'  # noqa: FS003
REPO_ARCHIVE = (f'repo::{DEFAULT_ARCHIVE_NAME}',)


def test_make_base_create_produces_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_patterns_file_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    mock_pattern_file = flexmock(name='/tmp/patterns')
    flexmock(module).should_receive('write_patterns_file').and_return(mock_pattern_file).and_return(
        None
    )
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    pattern_flags = ('--patterns-from', mock_pattern_file.name)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'patterns': ['pattern'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create') + pattern_flags
    assert create_positional_arguments == (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    assert pattern_file == mock_pattern_file


def test_make_base_create_command_with_store_config_false_omits_config_files():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'store_config_files': False,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


@pytest.mark.parametrize(
    'option_name,option_value,feature_available,option_flags',
    (
        ('checkpoint_interval', 600, True, ('--checkpoint-interval', '600')),
        ('checkpoint_volume', 1024, True, ('--checkpoint-volume', '1024')),
        ('chunker_params', '1,2,3,4', True, ('--chunker-params', '1,2,3,4')),
        ('compression', 'rle', True, ('--compression', 'rle')),
        ('one_file_system', True, True, ('--one-file-system',)),
        ('upload_rate_limit', 100, True, ('--upload-ratelimit', '100')),
        ('upload_rate_limit', 100, False, ('--remote-ratelimit', '100')),
        ('upload_buffer_size', 160, True, ('--upload-buffer', '160')),
        ('numeric_ids', True, True, ('--numeric-ids',)),
        ('numeric_ids', True, False, ('--numeric-owner',)),
        ('read_special', True, True, ('--read-special',)),
        ('ctime', True, True, ()),
        ('ctime', False, True, ('--noctime',)),
        ('birthtime', True, True, ()),
        ('birthtime', False, True, ('--nobirthtime',)),
        ('atime', True, True, ('--atime',)),
        ('atime', True, False, ()),
        ('atime', False, True, ()),
        ('atime', False, False, ('--noatime',)),
        ('flags', True, True, ()),
        ('flags', True, False, ()),
        ('flags', False, True, ('--noflags',)),
        ('flags', False, False, ('--nobsdflags',)),
        ('files_cache', 'ctime,size', True, ('--files-cache', 'ctime,size')),
        ('umask', 740, True, ('--umask', '740')),
        ('lock_wait', 5, True, ('--lock-wait', '5')),
    ),
)
def test_make_base_create_command_includes_configuration_option_as_command_flag(
    option_name, option_value, feature_available, option_flags
):
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(feature_available)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            option_name: option_value,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create') + option_flags
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_dry_run_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=True,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': ['exclude'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create', '--dry-run')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_local_path_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
        local_path='borg1',
    )

    assert create_flags == ('borg1', 'create')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_remote_path_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
        remote_path='borg1',
    )

    assert create_flags == ('borg', 'create', '--remote-path', 'borg1')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_log_json_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=True),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create', '--log-json')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_list_flags_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
        list_files=True,
    )

    assert create_flags == ('borg', 'create', '--list', '--filter', 'FOO')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_with_stream_processes_ignores_read_special_false_and_excludes_special_files():
    patterns = [Pattern('foo'), Pattern('bar')]
    patterns_file = flexmock(name='patterns')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').with_args(
        patterns, '/run/borgmatic', object
    ).and_return(patterns_file)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )
    flexmock(module.logger).should_receive('warning').twice()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('collect_special_file_paths').and_return(('/dev/null',)).once()
    flexmock(module).should_receive('write_patterns_file').with_args(
        (
            Pattern(
                '/dev/null',
                Pattern_type.EXCLUDE,
                Pattern_style.FNMATCH,
            ),
        ),
        '/run/borgmatic',
        'repo',
        patterns_file=patterns_file,
    ).and_return(patterns_file).once()
    flexmock(module).should_receive('make_exclude_flags').and_return(())

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'read_special': False,
        },
        patterns=patterns,
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
        stream_processes=flexmock(),
    )

    assert create_flags == ('borg', 'create', '--patterns-from', 'patterns', '--read-special')
    assert create_positional_arguments == REPO_ARCHIVE
    assert pattern_file


def test_make_base_create_command_without_patterns_and_with_stream_processes_ignores_read_special_false_and_excludes_special_files():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').with_args(
        [], '/run/borgmatic', object
    ).and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )
    flexmock(module.logger).should_receive('warning').twice()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('collect_special_file_paths').and_return(('/dev/null',)).once()
    flexmock(module).should_receive('write_patterns_file').with_args(
        (
            Pattern(
                '/dev/null',
                Pattern_type.EXCLUDE,
                Pattern_style.FNMATCH,
            ),
        ),
        '/run/borgmatic',
        'repo',
        patterns_file=None,
    ).and_return(flexmock(name='patterns')).once()
    flexmock(module).should_receive('make_exclude_flags').and_return(())

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': [],
            'repositories': ['repo'],
            'read_special': False,
        },
        patterns=[],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
        stream_processes=flexmock(),
    )

    assert create_flags == ('borg', 'create', '--read-special', '--patterns-from', 'patterns')
    assert create_positional_arguments == REPO_ARCHIVE
    assert pattern_file


def test_make_base_create_command_with_stream_processes_and_read_special_true_skips_special_files_excludes():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module).should_receive('collect_special_file_paths').never()

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'read_special': True,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
        stream_processes=flexmock(),
    )

    assert create_flags == ('borg', 'create', '--read-special')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_includes_archive_name_format_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::ARCHIVE_NAME',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'archive_name_format': 'ARCHIVE_NAME',
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == ('repo::ARCHIVE_NAME',)
    assert not pattern_file


def test_make_base_create_command_includes_default_archive_name_format_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::{hostname}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == ('repo::{hostname}',)
    assert not pattern_file


def test_make_base_create_command_includes_archive_name_format_with_placeholders_in_borg_command():
    repository_archive_pattern = 'repo::Documents_{hostname}-{now}'  # noqa: FS003
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (repository_archive_pattern,)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'archive_name_format': 'Documents_{hostname}-{now}',  # noqa: FS003
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == (repository_archive_pattern,)
    assert not pattern_file


def test_make_base_create_command_includes_repository_and_archive_name_format_with_placeholders_in_borg_command():
    repository_archive_pattern = '{fqdn}::Documents_{hostname}-{now}'  # noqa: FS003
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (repository_archive_pattern,)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='{fqdn}',  # noqa: FS003
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['{fqdn}'],  # noqa: FS003
            'archive_name_format': 'Documents_{hostname}-{now}',  # noqa: FS003
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == (repository_archive_pattern,)
    assert not pattern_file


def test_make_base_create_command_includes_extra_borg_options_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('write_patterns_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file) = module.make_base_create_command(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'extra_borg_options': {'create': '--extra --options'},
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/run/borgmatic',
    )

    assert create_flags == ('borg', 'create', '--extra', '--options')
    assert create_positional_arguments == REPO_ARCHIVE
    assert not pattern_file


def test_make_base_create_command_with_non_existent_directory_and_source_directories_must_exist_raises():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('check_all_root_patterns_exist').and_raise(ValueError)

    with pytest.raises(ValueError):
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'source_directories_must_exist': True,
            },
            patterns=[Pattern('foo'), Pattern('bar')],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_create_archive_calls_borg_with_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_create_archive_calls_borg_with_environment():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    environment = {'BORG_THINGY': 'YUP'}
    flexmock(module.environment).should_receive('make_environment').and_return(environment)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=environment,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_create_archive_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--info') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )
    insert_logging_mock(logging.INFO)

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_create_archive_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE,
        working_directory=None,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.INFO)

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        json=True,
    )


def test_create_archive_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--debug', '--show-rc') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )
    insert_logging_mock(logging.DEBUG)

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_create_archive_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE,
        working_directory=None,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    )
    insert_logging_mock(logging.DEBUG)

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        json=True,
    )


def test_create_archive_with_stats_and_dry_run_calls_borg_without_stats():
    # --dry-run and --stats are mutually exclusive, see:
    # https://borgbackup.readthedocs.io/en/stable/usage/create.html#description
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create', '--dry-run'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--dry-run', '--info') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )
    insert_logging_mock(logging.INFO)

    module.create_archive(
        dry_run=True,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        stats=True,
    )


def test_create_archive_with_working_directory_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir'
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory='/working/dir',
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'working_directory': '/working/dir',
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_create_archive_with_exit_codes_calls_borg_using_them():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    borg_exit_codes = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=borg_exit_codes,
        working_directory=None,
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
            'borg_exit_codes': borg_exit_codes,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_create_archive_with_stats_calls_borg_with_stats_parameter_and_answer_output_log_level():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--stats') + REPO_ARCHIVE,
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        stats=True,
    )


def test_create_archive_with_files_calls_borg_with_answer_output_log_level():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (
            ('borg', 'create', '--list', '--filter', 'FOO'),
            REPO_ARCHIVE,
            flexmock(),
        )
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--list', '--filter', 'FOO') + REPO_ARCHIVE,
        output_log_level=module.borgmatic.logger.ANSWER,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        list_files=True,
    )


def test_create_archive_with_progress_and_log_info_calls_borg_with_progress_parameter_and_no_list():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--info', '--progress') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )
    insert_logging_mock(logging.INFO)

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        progress=True,
    )


def test_create_archive_with_progress_calls_borg_with_progress_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--progress') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        progress=True,
    )


def test_create_archive_with_progress_and_stream_processes_calls_borg_with_progress_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    processes = flexmock()
    flexmock(module).should_receive('make_base_create_command').and_return(
        (
            ('borg', 'create', '--read-special'),
            REPO_ARCHIVE,
            flexmock(),
        )
    )
    flexmock(module.environment).should_receive('make_environment')
    create_command = (
        'borg',
        'create',
        '--read-special',
        '--progress',
    ) + REPO_ARCHIVE
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        create_command + ('--dry-run', '--list'),
        processes=processes,
        output_log_level=logging.INFO,
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        create_command,
        processes=processes,
        output_log_level=logging.INFO,
        output_file=module.DO_NOT_CAPTURE,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory=None,
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        progress=True,
        stream_processes=processes,
    )


def test_create_archive_with_json_calls_borg_with_json_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE,
        working_directory=None,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return('[]')

    json_output = module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        json=True,
    )

    assert json_output == '[]'


def test_create_archive_with_stats_and_json_calls_borg_without_stats_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE,
        working_directory=None,
        extra_environment=None,
        borg_local_path='borg',
        borg_exit_codes=None,
    ).and_return('[]')

    json_output = module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo*'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
        json=True,
        stats=True,
    )

    assert json_output == '[]'


def test_create_archive_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE, flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir'
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE,
        output_log_level=logging.INFO,
        output_file=None,
        borg_local_path='borg',
        borg_exit_codes=None,
        working_directory='/working/dir',
        extra_environment=None,
    )

    module.create_archive(
        dry_run=False,
        repository_path='repo',
        config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
            'working_directory': '/working/dir',
        },
        patterns=[Pattern('foo'), Pattern('bar')],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        borgmatic_runtime_directory='/borgmatic/run',
    )


def test_check_all_root_patterns_exist_with_existent_pattern_path_does_not_raise():
    flexmock(module.os.path).should_receive('exists').and_return(True)

    module.check_all_root_patterns_exist([Pattern('foo')])


def test_check_all_root_patterns_exist_with_non_root_pattern_skips_existence_check():
    flexmock(module.os.path).should_receive('exists').never()

    module.check_all_root_patterns_exist([Pattern('foo', Pattern_type.INCLUDE)])


def test_check_all_root_patterns_exist_with_non_existent_pattern_path_raises():
    flexmock(module.os.path).should_receive('exists').and_return(False)

    with pytest.raises(ValueError):
        module.check_all_root_patterns_exist([Pattern('foo')])
