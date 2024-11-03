import logging
import sys

import pytest
from flexmock import flexmock

from borgmatic.borg import create as module

from ..test_verbosity import insert_logging_mock


def test_expand_directory_with_basic_path_passes_it_through():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo')
    flexmock(module.glob).should_receive('glob').and_return([])

    paths = module.expand_directory('foo', None)

    assert paths == ['foo']


def test_expand_directory_with_glob_expands():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo*')
    flexmock(module.glob).should_receive('glob').and_return(['foo', 'food'])

    paths = module.expand_directory('foo*', None)

    assert paths == ['foo', 'food']


def test_expand_directory_with_working_directory_passes_it_through():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo').and_return([]).once()

    paths = module.expand_directory('foo', working_directory='/working/dir')

    assert paths == ['/working/dir/foo']


def test_expand_directory_with_glob_passes_through_working_directory():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo*')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo*').and_return(
        ['/working/dir/foo', '/working/dir/food']
    ).once()

    paths = module.expand_directory('foo*', working_directory='/working/dir')

    assert paths == ['/working/dir/foo', '/working/dir/food']


def test_expand_directories_flattens_expanded_directories():
    flexmock(module).should_receive('expand_directory').with_args('~/foo', None).and_return(
        ['/root/foo']
    )
    flexmock(module).should_receive('expand_directory').with_args('bar*', None).and_return(
        ['bar', 'barf']
    )

    paths = module.expand_directories(('~/foo', 'bar*'))

    assert paths == ('/root/foo', 'bar', 'barf')


def test_expand_directories_with_working_directory_passes_it_through():
    flexmock(module).should_receive('expand_directory').with_args('foo', '/working/dir').and_return(
        ['/working/dir/foo']
    )

    paths = module.expand_directories(('foo',), working_directory='/working/dir')

    assert paths == ('/working/dir/foo',)


def test_expand_directories_considers_none_as_no_directories():
    paths = module.expand_directories(None, None)

    assert paths == ()


def test_expand_home_directories_expands_tildes():
    flexmock(module.os.path).should_receive('expanduser').with_args('~/bar').and_return('/foo/bar')
    flexmock(module.os.path).should_receive('expanduser').with_args('baz').and_return('baz')

    paths = module.expand_home_directories(('~/bar', 'baz'))

    assert paths == ('/foo/bar', 'baz')


def test_expand_home_directories_considers_none_as_no_directories():
    paths = module.expand_home_directories(None)

    assert paths == ()


def test_map_directories_to_devices_gives_device_id_per_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').and_return(flexmock(st_dev=66))

    device_map = module.map_directories_to_devices(('/foo', '/bar'))

    assert device_map == {
        '/foo': 55,
        '/bar': 66,
    }


def test_map_directories_to_devices_with_missing_path_does_not_error():
    flexmock(module.os.path).should_receive('exists').and_return(True).and_return(False)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').never()

    device_map = module.map_directories_to_devices(('/foo', '/bar'))

    assert device_map == {
        '/foo': 55,
        '/bar': None,
    }


def test_map_directories_to_devices_uses_working_directory_to_construct_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/working/dir/bar').and_return(
        flexmock(st_dev=66)
    )

    device_map = module.map_directories_to_devices(
        ('/foo', 'bar'), working_directory='/working/dir'
    )

    assert device_map == {
        '/foo': 55,
        'bar': 66,
    }


@pytest.mark.parametrize(
    'directories,additional_directories,expected_directories',
    (
        ({'/': 1, '/root': 1}, {}, ('/',)),
        ({'/': 1, '/root/': 1}, {}, ('/',)),
        ({'/': 1, '/root': 2}, {}, ('/', '/root')),
        ({'/root': 1, '/': 1}, {}, ('/',)),
        ({'/root': 1, '/root/foo': 1}, {}, ('/root',)),
        ({'/root/': 1, '/root/foo': 1}, {}, ('/root/',)),
        ({'/root': 1, '/root/foo/': 1}, {}, ('/root',)),
        ({'/root': 1, '/root/foo': 2}, {}, ('/root', '/root/foo')),
        ({'/root/foo': 1, '/root': 1}, {}, ('/root',)),
        ({'/root': None, '/root/foo': None}, {}, ('/root', '/root/foo')),
        ({'/root': 1, '/etc': 1, '/root/foo/bar': 1}, {}, ('/etc', '/root')),
        ({'/root': 1, '/root/foo': 1, '/root/foo/bar': 1}, {}, ('/root',)),
        ({'/dup': 1, '/dup': 1}, {}, ('/dup',)),
        ({'/foo': 1, '/bar': 1}, {}, ('/bar', '/foo')),
        ({'/foo': 1, '/bar': 2}, {}, ('/bar', '/foo')),
        ({'/root/foo': 1}, {'/root': 1}, ()),
        ({'/root/foo': 1}, {'/root': 2}, ('/root/foo',)),
        ({'/root/foo': 1}, {}, ('/root/foo',)),
    ),
)
def test_deduplicate_directories_removes_child_paths_on_the_same_filesystem(
    directories, additional_directories, expected_directories
):
    assert (
        module.deduplicate_directories(directories, additional_directories) == expected_directories
    )


def test_write_pattern_file_writes_pattern_lines():
    temporary_file = flexmock(name='filename', flush=lambda: None)
    temporary_file.should_receive('write').with_args('R /foo\n+ /foo/bar')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').and_return(temporary_file)

    module.write_pattern_file(['R /foo', '+ /foo/bar'])


def test_write_pattern_file_with_sources_writes_sources_as_roots():
    temporary_file = flexmock(name='filename', flush=lambda: None)
    temporary_file.should_receive('write').with_args('R /foo\n+ /foo/bar\nR /baz\nR /quux')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').and_return(temporary_file)

    module.write_pattern_file(['R /foo', '+ /foo/bar'], sources=['/baz', '/quux'])


def test_write_pattern_file_without_patterns_but_with_sources_writes_sources_as_roots():
    temporary_file = flexmock(name='filename', flush=lambda: None)
    temporary_file.should_receive('write').with_args('R /baz\nR /quux')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').and_return(temporary_file)

    module.write_pattern_file([], sources=['/baz', '/quux'])


def test_write_pattern_file_with_empty_exclude_patterns_does_not_raise():
    module.write_pattern_file([])


def test_write_pattern_file_overwrites_existing_file():
    pattern_file = flexmock(name='filename', flush=lambda: None)
    pattern_file.should_receive('seek').with_args(0).once()
    pattern_file.should_receive('write').with_args('R /foo\n+ /foo/bar')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').never()

    module.write_pattern_file(['R /foo', '+ /foo/bar'], pattern_file=pattern_file)


@pytest.mark.parametrize(
    'filename_lists,opened_filenames',
    (
        ([('foo', 'bar'), ('baz', 'quux')], ('foo', 'bar', 'baz', 'quux')),
        ([None, ('foo', 'bar')], ('foo', 'bar')),
        ([None, None], ()),
    ),
)
def test_ensure_files_readable_opens_filenames(filename_lists, opened_filenames):
    for expected_filename in opened_filenames:
        flexmock(sys.modules['builtins']).should_receive('open').with_args(
            expected_filename
        ).and_return(flexmock(close=lambda: None))

    module.ensure_files_readable(*filename_lists)


def test_make_pattern_flags_includes_pattern_filename_when_given():
    pattern_flags = module.make_pattern_flags(
        config={'patterns': ['R /', '- /var']}, pattern_filename='/tmp/patterns'
    )

    assert pattern_flags == ('--patterns-from', '/tmp/patterns')


def test_make_pattern_flags_includes_patterns_from_filenames_when_in_config():
    pattern_flags = module.make_pattern_flags(config={'patterns_from': ['patterns', 'other']})

    assert pattern_flags == ('--patterns-from', 'patterns', '--patterns-from', 'other')


def test_make_pattern_flags_includes_both_filenames_when_patterns_given_and_patterns_from_in_config():
    pattern_flags = module.make_pattern_flags(
        config={'patterns_from': ['patterns']}, pattern_filename='/tmp/patterns'
    )

    assert pattern_flags == ('--patterns-from', 'patterns', '--patterns-from', '/tmp/patterns')


def test_make_pattern_flags_considers_none_patterns_from_filenames_as_empty():
    pattern_flags = module.make_pattern_flags(config={'patterns_from': None})

    assert pattern_flags == ()


def test_make_exclude_flags_includes_exclude_patterns_filename_when_given():
    exclude_flags = module.make_exclude_flags(
        config={'exclude_patterns': ['*.pyc', '/var']}, exclude_filename='/tmp/excludes'
    )

    assert exclude_flags == ('--exclude-from', '/tmp/excludes')


def test_make_exclude_flags_includes_exclude_from_filenames_when_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_from': ['excludes', 'other']})

    assert exclude_flags == ('--exclude-from', 'excludes', '--exclude-from', 'other')


def test_make_exclude_flags_includes_both_filenames_when_patterns_given_and_exclude_from_in_config():
    exclude_flags = module.make_exclude_flags(
        config={'exclude_from': ['excludes']}, exclude_filename='/tmp/excludes'
    )

    assert exclude_flags == ('--exclude-from', 'excludes', '--exclude-from', '/tmp/excludes')


def test_make_exclude_flags_considers_none_exclude_from_filenames_as_empty():
    exclude_flags = module.make_exclude_flags(config={'exclude_from': None})

    assert exclude_flags == ()


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


def test_collect_borgmatic_runtime_directories_set_when_directory_exists():
    flexmock(module.os.path).should_receive('exists').and_return(True)

    assert module.collect_borgmatic_runtime_directories('/tmp') == ['/tmp']


def test_collect_borgmatic_runtime_directories_empty_when_directory_does_not_exist():
    flexmock(module.os.path).should_receive('exists').and_return(False)

    assert module.collect_borgmatic_runtime_directories('/tmp') == []


def test_pattern_root_directories_deals_with_none_patterns():
    assert module.pattern_root_directories(patterns=None) == []


def test_pattern_root_directories_parses_roots_and_ignores_others():
    assert module.pattern_root_directories(
        ['R /root', '+ /root/foo', '- /root/foo/bar', 'R /baz']
    ) == ['/root', '/baz']


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
    flexmock(module).should_receive('any_parent_directories').and_return(False)

    assert module.collect_special_file_paths(
        ('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        skip_directories=flexmock(),
    ) == ('/foo', '/bar', '/baz')


def test_collect_special_file_paths_excludes_requested_directories():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '+ /foo\n- /bar\n- /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True)
    flexmock(module).should_receive('any_parent_directories').and_return(False).and_return(
        True
    ).and_return(False)

    assert module.collect_special_file_paths(
        ('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        skip_directories=flexmock(),
    ) == ('/foo', '/baz')


def test_collect_special_file_paths_excludes_non_special_files():
    flexmock(module).should_receive('execute_command_and_capture_output').and_return(
        '+ /foo\n+ /bar\n+ /baz'
    )
    flexmock(module).should_receive('special_file').and_return(True).and_return(False).and_return(
        True
    )
    flexmock(module).should_receive('any_parent_directories').and_return(False)

    assert module.collect_special_file_paths(
        ('borg', 'create'),
        config={},
        local_path=None,
        working_directory=None,
        borg_environment=None,
        skip_directories=flexmock(),
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
    flexmock(module).should_receive('any_parent_directories').and_return(False)

    module.collect_special_file_paths(
        ('borg', 'create', '--exclude-nodump'),
        config={},
        local_path='borg',
        working_directory=None,
        borg_environment=None,
        skip_directories=flexmock(),
    )


DEFAULT_ARCHIVE_NAME = '{hostname}-{now:%Y-%m-%dT%H:%M:%S.%f}'  # noqa: FS003
REPO_ARCHIVE_WITH_PATHS = (f'repo::{DEFAULT_ARCHIVE_NAME}', 'foo', 'bar')


def test_make_base_create_produces_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_patterns_file_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    mock_pattern_file = flexmock(name='/tmp/patterns')
    flexmock(module).should_receive('write_pattern_file').and_return(mock_pattern_file).and_return(
        None
    )
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    pattern_flags = ('--patterns-from', mock_pattern_file.name)
    flexmock(module).should_receive('make_pattern_flags').and_return(pattern_flags)
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'patterns': ['pattern'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create') + pattern_flags
    assert create_positional_arguments == (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    assert pattern_file == mock_pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_sources_and_config_paths_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(
        ('foo', 'bar', '/tmp/test.yaml')
    )
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').with_args([], None).and_return(())
    flexmock(module).should_receive('expand_directories').with_args(
        ('foo', 'bar', '/tmp/test.yaml'),
        None,
    ).and_return(('foo', 'bar', '/tmp/test.yaml'))
    flexmock(module).should_receive('expand_directories').with_args([], None).and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS + ('/tmp/test.yaml',)
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_with_store_config_false_omits_config_files():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').with_args([], None).and_return(())
    flexmock(module).should_receive('expand_directories').with_args(
        ('foo', 'bar'), None
    ).and_return(('foo', 'bar'))
    flexmock(module).should_receive('expand_directories').with_args([], None).and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'store_config_files': False,
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_exclude_patterns_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(('exclude',))
    mock_exclude_file = flexmock(name='/tmp/excludes')
    flexmock(module).should_receive('write_pattern_file').and_return(mock_exclude_file)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    exclude_flags = ('--exclude-from', 'excludes')
    flexmock(module).should_receive('make_exclude_flags').and_return(exclude_flags)
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'exclude_patterns': ['exclude'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create') + exclude_flags
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert exclude_file == mock_exclude_file


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
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(feature_available)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                option_name: option_value,
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create') + option_flags
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_dry_run_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=True,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'exclude_patterns': ['exclude'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create', '--dry-run')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_local_path_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
            local_path='borg1',
        )
    )

    assert create_flags == ('borg1', 'create')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_remote_path_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
            remote_path='borg1',
        )
    )

    assert create_flags == ('borg', 'create', '--remote-path', 'borg1')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_log_json_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=True),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create', '--log-json')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_list_flags_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
            list_files=True,
        )
    )

    assert create_flags == ('borg', 'create', '--list', '--filter', 'FOO')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_with_stream_processes_ignores_read_special_false_and_excludes_special_files():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )
    flexmock(module.logger).should_receive('warning').twice()
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module).should_receive('collect_special_file_paths').and_return(('/dev/null',)).once()
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(flexmock(name='patterns'))
    flexmock(module).should_receive('make_exclude_flags').and_return(())

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'read_special': False,
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
            stream_processes=flexmock(),
        )
    )

    assert create_flags == ('borg', 'create', '--read-special')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert exclude_file


def test_make_base_create_command_with_stream_processes_and_read_special_true_skip_special_files_excludes():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )
    flexmock(module.logger).should_receive('warning').never()
    flexmock(module).should_receive('collect_special_file_paths').never()

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'read_special': True,
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
            stream_processes=flexmock(),
        )
    )

    assert create_flags == ('borg', 'create', '--read-special')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_with_non_matching_source_directories_glob_passes_through():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo*',))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo*'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == (f'repo::{DEFAULT_ARCHIVE_NAME}', 'foo*')
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_expands_glob_in_source_directories():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'food'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo*'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == (f'repo::{DEFAULT_ARCHIVE_NAME}', 'foo', 'food')
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_archive_name_format_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::ARCHIVE_NAME',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'archive_name_format': 'ARCHIVE_NAME',
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == ('repo::ARCHIVE_NAME', 'foo', 'bar')
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_default_archive_name_format_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        ('repo::{hostname}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == ('repo::{hostname}', 'foo', 'bar')
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_archive_name_format_with_placeholders_in_borg_command():
    repository_archive_pattern = 'repo::Documents_{hostname}-{now}'  # noqa: FS003
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (repository_archive_pattern,)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'archive_name_format': 'Documents_{hostname}-{now}',  # noqa: FS003
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == (repository_archive_pattern, 'foo', 'bar')
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_repository_and_archive_name_format_with_placeholders_in_borg_command():
    repository_archive_pattern = '{fqdn}::Documents_{hostname}-{now}'  # noqa: FS003
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (repository_archive_pattern,)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='{fqdn}',  # noqa: FS003
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['{fqdn}'],  # noqa: FS003
                'archive_name_format': 'Documents_{hostname}-{now}',  # noqa: FS003
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create')
    assert create_positional_arguments == (repository_archive_pattern, 'foo', 'bar')
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_includes_extra_borg_options_in_borg_command():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module).should_receive('pattern_root_directories').and_return([])
    flexmock(module.os.path).should_receive('expanduser').and_raise(TypeError)
    flexmock(module).should_receive('expand_home_directories').and_return(())
    flexmock(module).should_receive('write_pattern_file').and_return(None)
    flexmock(module).should_receive('make_list_filter_flags').and_return('FOO')
    flexmock(module.flags).should_receive('get_default_archive_name_format').and_return(
        '{hostname}'
    )
    flexmock(module.feature).should_receive('available').and_return(True)
    flexmock(module).should_receive('ensure_files_readable')
    flexmock(module).should_receive('make_pattern_flags').and_return(())
    flexmock(module).should_receive('make_exclude_flags').and_return(())
    flexmock(module.flags).should_receive('make_repository_archive_flags').and_return(
        (f'repo::{DEFAULT_ARCHIVE_NAME}',)
    )

    (create_flags, create_positional_arguments, pattern_file, exclude_file) = (
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'extra_borg_options': {'create': '--extra --options'},
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )
    )

    assert create_flags == ('borg', 'create', '--extra', '--options')
    assert create_positional_arguments == REPO_ARCHIVE_WITH_PATHS
    assert not pattern_file
    assert not exclude_file


def test_make_base_create_command_with_non_existent_directory_and_source_directories_must_exist_raises():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('check_all_source_directories_exist').and_raise(ValueError)

    with pytest.raises(ValueError):
        module.make_base_create_command(
            dry_run=False,
            repository_path='repo',
            config={
                'source_directories': ['foo', 'bar'],
                'repositories': ['repo'],
                'source_directories_must_exist': True,
            },
            config_paths=['/tmp/test.yaml'],
            local_borg_version='1.2.3',
            global_arguments=flexmock(log_json=False),
            borgmatic_runtime_directories=(),
        )


def test_create_archive_calls_borg_with_parameters():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_create_archive_calls_borg_with_environment():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    environment = {'BORG_THINGY': 'YUP'}
    flexmock(module.environment).should_receive('make_environment').and_return(environment)
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_create_archive_with_log_info_calls_borg_with_info_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--info') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_create_archive_with_log_info_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        json=True,
    )


def test_create_archive_with_log_debug_calls_borg_with_debug_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--debug', '--show-rc') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_create_archive_with_log_debug_and_json_suppresses_most_borg_output():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        json=True,
    )


def test_create_archive_with_stats_and_dry_run_calls_borg_without_stats():
    # --dry-run and --stats are mutually exclusive, see:
    # https://borgbackup.readthedocs.io/en/stable/usage/create.html#description
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create', '--dry-run'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--dry-run', '--info') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        stats=True,
    )


def test_create_archive_with_working_directory_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir'
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_create_archive_with_exit_codes_calls_borg_using_them():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    borg_exit_codes = flexmock()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_create_archive_with_stats_calls_borg_with_stats_parameter_and_answer_output_log_level():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--stats') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        stats=True,
    )


def test_create_archive_with_files_calls_borg_with_answer_output_log_level():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (
            ('borg', 'create', '--list', '--filter', 'FOO'),
            REPO_ARCHIVE_WITH_PATHS,
            flexmock(),
            flexmock(),
        )
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--list', '--filter', 'FOO') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        list_files=True,
    )


def test_create_archive_with_progress_and_log_info_calls_borg_with_progress_parameter_and_no_list():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--info', '--progress') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        progress=True,
    )


def test_create_archive_with_progress_calls_borg_with_progress_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create', '--progress') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        progress=True,
    )


def test_create_archive_with_progress_and_stream_processes_calls_borg_with_progress_parameter():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    processes = flexmock()
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (
            ('borg', 'create', '--read-special'),
            REPO_ARCHIVE_WITH_PATHS,
            flexmock(),
            flexmock(),
        )
    )
    flexmock(module.environment).should_receive('make_environment')
    create_command = (
        'borg',
        'create',
        '--read-special',
        '--progress',
    ) + REPO_ARCHIVE_WITH_PATHS
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        progress=True,
        stream_processes=processes,
    )


def test_create_archive_with_json_calls_borg_with_json_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        json=True,
    )

    assert json_output == '[]'


def test_create_archive_with_stats_and_json_calls_borg_without_stats_flag():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_and_capture_output').with_args(
        ('borg', 'create', '--json') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
        json=True,
        stats=True,
    )

    assert json_output == '[]'


def test_create_archive_calls_borg_with_working_directory():
    flexmock(module.borgmatic.logger).should_receive('add_custom_log_levels')
    flexmock(module.logging).ANSWER = module.borgmatic.logger.ANSWER
    flexmock(module).should_receive('expand_directories').and_return(())
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_runtime_directory'
    ).and_return('/var/run/0/borgmatic')
    flexmock(module).should_receive('collect_borgmatic_runtime_directories').and_return([])
    flexmock(module).should_receive('make_base_create_command').and_return(
        (('borg', 'create'), REPO_ARCHIVE_WITH_PATHS, flexmock(), flexmock())
    )
    flexmock(module.environment).should_receive('make_environment')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir'
    )
    flexmock(module).should_receive('execute_command').with_args(
        ('borg', 'create') + REPO_ARCHIVE_WITH_PATHS,
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
        config_paths=['/tmp/test.yaml'],
        local_borg_version='1.2.3',
        global_arguments=flexmock(log_json=False),
    )


def test_check_all_source_directories_exist_with_glob_and_tilde_directories():
    flexmock(module).should_receive('expand_directory').with_args('foo*', None).and_return(
        ('foo', 'food')
    )
    flexmock(module).should_receive('expand_directory').with_args('~/bar', None).and_return(
        ('/root/bar',)
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('food').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/root/bar').and_return(True)

    module.check_all_source_directories_exist(['foo*', '~/bar'])


def test_check_all_source_directories_exist_with_non_existent_directory_raises():
    flexmock(module).should_receive('expand_directory').with_args('foo', None).and_return(('foo',))
    flexmock(module.os.path).should_receive('exists').and_return(False)

    with pytest.raises(ValueError):
        module.check_all_source_directories_exist(['foo'])


def test_check_all_source_directories_exist_with_working_directory_applies_to_relative_source_directories():
    flexmock(module).should_receive('expand_directory').with_args(
        'foo*', working_directory='/tmp'
    ).and_return(('/tmp/foo', '/tmp/food'))
    flexmock(module).should_receive('expand_directory').with_args(
        '/root/bar', working_directory='/tmp'
    ).and_return(('/root/bar',))
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os.path).should_receive('exists').with_args('/tmp/foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/tmp/food').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/root/bar').and_return(True)

    module.check_all_source_directories_exist(['foo*', '/root/bar'], working_directory='/tmp')
