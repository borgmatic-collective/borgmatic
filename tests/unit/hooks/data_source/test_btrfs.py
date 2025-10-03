import pytest
from flexmock import flexmock

from borgmatic.borg.pattern import Pattern, Pattern_source, Pattern_style, Pattern_type
from borgmatic.hooks.data_source import btrfs as module


def test_path_is_a_subvolume_with_btrfs_success_call_returns_true():
    module.path_is_a_subvolume.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command',
    ).with_args(('btrfs', 'subvolume', 'show', '/mnt0'), output_log_level=None, close_fds=True)

    assert module.path_is_a_subvolume('btrfs', '/mnt0') is True


def test_path_is_a_subvolume_with_btrfs_error_returns_false():
    module.path_is_a_subvolume.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command',
    ).with_args(
        ('btrfs', 'subvolume', 'show', '/mnt0'), output_log_level=None, close_fds=True
    ).and_raise(
        module.subprocess.CalledProcessError(1, 'btrfs'),
    )

    assert module.path_is_a_subvolume('btrfs', '/mnt0') is False


def test_path_is_a_subvolume_caches_result_after_first_call():
    module.path_is_a_subvolume.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command',
    ).once()

    assert module.path_is_a_subvolume('btrfs', '/mnt0') is True
    assert module.path_is_a_subvolume('btrfs', '/mnt0') is True


def test_get_subvolume_property_with_invalid_btrfs_output_errors():
    module.get_subvolume_property.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('invalid')

    with pytest.raises(ValueError):
        module.get_subvolume_property('btrfs', '/foo', 'ro')


def test_get_subvolume_property_with_true_output_returns_true_bool():
    module.get_subvolume_property.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('ro=true')

    assert module.get_subvolume_property('btrfs', '/foo', 'ro') is True


def test_get_subvolume_property_with_false_output_returns_false_bool():
    module.get_subvolume_property.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('ro=false')

    assert module.get_subvolume_property('btrfs', '/foo', 'ro') is False


def test_get_subvolume_property_passes_through_general_value():
    module.get_subvolume_property.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('thing=value')

    assert module.get_subvolume_property('btrfs', '/foo', 'thing') == 'value'


def test_get_subvolume_property_caches_result_after_first_call():
    module.get_subvolume_property.cache_clear()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_return('thing=value').once()

    assert module.get_subvolume_property('btrfs', '/foo', 'thing') == 'value'
    assert module.get_subvolume_property('btrfs', '/foo', 'thing') == 'value'


def test_get_containing_subvolume_path_with_subvolume_self_returns_it():
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar/baz'
    ).and_return(True)
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/foo/bar').never()
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/foo').never()
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/').never()
    flexmock(module).should_receive('get_subvolume_property').and_return(False)

    assert module.get_containing_subvolume_path('btrfs', '/foo/bar/baz') == '/foo/bar/baz'


def test_get_containing_subvolume_path_with_subvolume_parent_returns_it():
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar/baz'
    ).and_return(False)
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar'
    ).and_return(True)
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/foo').never()
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/').never()
    flexmock(module).should_receive('get_subvolume_property').and_return(False)

    assert module.get_containing_subvolume_path('btrfs', '/foo/bar/baz') == '/foo/bar'


def test_get_containing_subvolume_path_with_subvolume_grandparent_returns_it():
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar/baz'
    ).and_return(False)
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar'
    ).and_return(False)
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/foo').and_return(
        True
    )
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/').never()
    flexmock(module).should_receive('get_subvolume_property').and_return(False)

    assert module.get_containing_subvolume_path('btrfs', '/foo/bar/baz') == '/foo'


def test_get_containing_subvolume_path_without_subvolume_ancestor_returns_none():
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar/baz'
    ).and_return(False)
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar'
    ).and_return(False)
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/foo').and_return(
        False
    )
    flexmock(module).should_receive('path_is_a_subvolume').with_args('btrfs', '/').and_return(False)
    flexmock(module).should_receive('get_subvolume_property').and_return(False)

    assert module.get_containing_subvolume_path('btrfs', '/foo/bar/baz') is None


def test_get_containing_subvolume_path_with_read_only_subvolume_returns_none():
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar/baz'
    ).and_return(True)
    flexmock(module).should_receive('get_subvolume_property').and_return(True)

    assert module.get_containing_subvolume_path('btrfs', '/foo/bar/baz') is None


def test_get_containing_subvolume_path_with_read_only_error_returns_none():
    flexmock(module).should_receive('path_is_a_subvolume').with_args(
        'btrfs', '/foo/bar/baz'
    ).and_return(True)
    flexmock(module).should_receive('get_subvolume_property').and_raise(
        module.subprocess.CalledProcessError(1, 'wtf')
    )

    assert module.get_containing_subvolume_path('btrfs', '/foo/bar/baz') is None


def test_get_all_subvolume_paths_skips_non_root_and_non_config_patterns():
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/foo'
    ).never()
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/bar'
    ).and_return('/bar').once()
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/baz'
    ).never()

    assert module.get_all_subvolume_paths(
        'btrfs',
        (
            module.borgmatic.borg.pattern.Pattern(
                '/foo',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
            ),
            module.borgmatic.borg.pattern.Pattern(
                '/bar',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
            module.borgmatic.borg.pattern.Pattern(
                '/baz',
                type=module.borgmatic.borg.pattern.Pattern_type.INCLUDE,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
        ),
    ) == ('/bar',)


def test_get_all_subvolume_paths_skips_non_btrfs_patterns():
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/foo'
    ).and_return(None).once()
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/bar'
    ).and_return('/bar').once()

    assert module.get_all_subvolume_paths(
        'btrfs',
        (
            module.borgmatic.borg.pattern.Pattern(
                '/foo',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
            module.borgmatic.borg.pattern.Pattern(
                '/bar',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
        ),
    ) == ('/bar',)


def test_get_all_subvolume_paths_sorts_subvolume_paths():
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/foo'
    ).and_return('/foo').once()
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/bar'
    ).and_return('/bar').once()
    flexmock(module).should_receive('get_containing_subvolume_path').with_args(
        'btrfs', '/baz'
    ).and_return('/baz').once()

    assert module.get_all_subvolume_paths(
        'btrfs',
        (
            module.borgmatic.borg.pattern.Pattern(
                '/foo',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
            module.borgmatic.borg.pattern.Pattern(
                '/bar',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
            module.borgmatic.borg.pattern.Pattern(
                '/baz',
                type=module.borgmatic.borg.pattern.Pattern_type.ROOT,
                source=module.borgmatic.borg.pattern.Pattern_source.CONFIG,
            ),
        ),
    ) == ('/bar', '/baz', '/foo')


def test_get_subvolumes_collects_subvolumes_matching_patterns():
    flexmock(module).should_receive('get_all_subvolume_paths').and_return(('/mnt1', '/mnt2'))

    contained_pattern = Pattern(
        '/mnt1',
        type=Pattern_type.ROOT,
        source=Pattern_source.CONFIG,
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/mnt1', object).and_return((contained_pattern,))
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/mnt2', object).and_return(())

    assert module.get_subvolumes(
        'btrfs',
        patterns=[
            Pattern('/mnt1'),
            Pattern('/mnt3'),
        ],
    ) == (module.Subvolume('/mnt1', contained_patterns=(contained_pattern,)),)


def test_get_subvolumes_skips_non_root_patterns():
    flexmock(module).should_receive('get_all_subvolume_paths').and_return(('/mnt1', '/mnt2'))

    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/mnt1', object).and_return(
        (
            Pattern(
                '/mnt1',
                type=Pattern_type.EXCLUDE,
                source=Pattern_source.CONFIG,
            ),
        ),
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/mnt2', object).and_return(())

    assert (
        module.get_subvolumes(
            'btrfs',
            patterns=[
                Pattern('/mnt1'),
                Pattern('/mnt3'),
            ],
        )
        == ()
    )


def test_get_subvolumes_skips_non_config_patterns():
    flexmock(module).should_receive('get_all_subvolume_paths').and_return(('/mnt1', '/mnt2'))

    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/mnt1', object).and_return(
        (
            Pattern(
                '/mnt1',
                type=Pattern_type.ROOT,
                source=Pattern_source.HOOK,
            ),
        ),
    )
    flexmock(module.borgmatic.hooks.data_source.snapshot).should_receive(
        'get_contained_patterns',
    ).with_args('/mnt2', object).and_return(())

    assert (
        module.get_subvolumes(
            'btrfs',
            patterns=[
                Pattern('/mnt1'),
                Pattern('/mnt3'),
            ],
        )
        == ()
    )


@pytest.mark.parametrize(
    'subvolume_path,expected_snapshot_path',
    (
        ('/foo/bar', '/foo/bar/.borgmatic-snapshot-1234/foo/bar'),
        ('/', '/.borgmatic-snapshot-1234'),
    ),
)
def test_make_snapshot_path_includes_stripped_subvolume_path(
    subvolume_path,
    expected_snapshot_path,
):
    flexmock(module.os).should_receive('getpid').and_return(1234)

    assert module.make_snapshot_path(subvolume_path) == expected_snapshot_path


@pytest.mark.parametrize(
    'subvolume_path,pattern,expected_pattern',
    (
        (
            '/foo/bar',
            Pattern('/foo/bar/baz'),
            Pattern('/foo/bar/.borgmatic-snapshot-1234/./foo/bar/baz'),
        ),
        ('/foo/bar', Pattern('/foo/bar'), Pattern('/foo/bar/.borgmatic-snapshot-1234/./foo/bar')),
        (
            '/foo/bar',
            Pattern('^/foo/bar', Pattern_type.INCLUDE, Pattern_style.REGULAR_EXPRESSION),
            Pattern(
                '^/foo/bar/.borgmatic-snapshot-1234/./foo/bar',
                Pattern_type.INCLUDE,
                Pattern_style.REGULAR_EXPRESSION,
            ),
        ),
        (
            '/foo/bar',
            Pattern('/foo/bar', Pattern_type.INCLUDE, Pattern_style.REGULAR_EXPRESSION),
            Pattern(
                '/foo/bar/.borgmatic-snapshot-1234/./foo/bar',
                Pattern_type.INCLUDE,
                Pattern_style.REGULAR_EXPRESSION,
            ),
        ),
        ('/', Pattern('/foo'), Pattern('/.borgmatic-snapshot-1234/./foo')),
        ('/', Pattern('/'), Pattern('/.borgmatic-snapshot-1234/./')),
        (
            '/foo/bar',
            Pattern('/foo/bar/./baz'),
            Pattern('/foo/bar/.borgmatic-snapshot-1234/foo/bar/./baz'),
        ),
    ),
)
def test_make_borg_snapshot_pattern_includes_slashdot_hack_and_stripped_pattern_path(
    subvolume_path,
    pattern,
    expected_pattern,
):
    flexmock(module.os).should_receive('getpid').and_return(1234)

    assert module.make_borg_snapshot_pattern(subvolume_path, pattern) == expected_pattern


def test_dump_data_sources_snapshots_each_subvolume_and_updates_patterns():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol1',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol2',
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1',
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    )
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol2',
    ).and_return(
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1',
        object,
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol2',
        object,
    ).and_return(Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
        Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'),
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {},
    }


def test_dump_data_sources_uses_custom_btrfs_command_in_commands():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {'btrfs_command': '/usr/local/bin/btrfs'}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        '/usr/local/bin/btrfs',
        '/mnt/subvol1',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1',
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1',
        object,
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {
            'btrfs_command': '/usr/local/bin/btrfs',
        },
    }


def test_dump_data_sources_with_findmnt_command_warns():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {'findmnt_command': '/usr/local/bin/findmnt'}}
    flexmock(module.logger).should_receive('warning').once()
    flexmock(module).should_receive('get_subvolumes').with_args(
        'btrfs',
        patterns,
    ).and_return(
        (module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),),
    ).once()
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol1',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1',
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1',
        object,
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {
            'findmnt_command': '/usr/local/bin/findmnt',
        },
    }


def test_dump_data_sources_with_dry_run_skips_snapshot_and_patterns_update():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    )
    flexmock(module).should_receive('snapshot_subvolume').never()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').never()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=True,
        )
        == []
    )

    assert patterns == [Pattern('/foo'), Pattern('/mnt/subvol1')]
    assert config == {'btrfs': {}}


def test_dump_data_sources_without_matching_subvolumes_skips_snapshot_and_patterns_update():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(())
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module).should_receive('snapshot_subvolume').never()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').never()

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [Pattern('/foo'), Pattern('/mnt/subvol1')]
    assert config == {'btrfs': {}}


def test_dump_data_sources_snapshots_adds_to_existing_exclude_patterns():
    patterns = [Pattern('/foo'), Pattern('/mnt/subvol1')]
    config = {'btrfs': {}, 'exclude_patterns': ['/bar']}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    )
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol1',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('snapshot_subvolume').with_args(
        'btrfs',
        '/mnt/subvol2',
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).once()
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol1',
    ).and_return(
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    )
    flexmock(module).should_receive('make_snapshot_exclude_pattern').with_args(
        '/mnt/subvol2',
    ).and_return(
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    )
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol1',
        object,
    ).and_return(Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'))
    flexmock(module).should_receive('make_borg_snapshot_pattern').with_args(
        '/mnt/subvol2',
        object,
    ).and_return(Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'))

    assert (
        module.dump_data_sources(
            hook_config=config['btrfs'],
            config=config,
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=patterns,
            dry_run=False,
        )
        == []
    )

    assert patterns == [
        Pattern('/foo'),
        Pattern('/mnt/subvol1/.borgmatic-1234/mnt/subvol1'),
        Pattern(
            '/mnt/subvol1/.borgmatic-1234/mnt/subvol1/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
        Pattern('/mnt/subvol2/.borgmatic-1234/mnt/subvol2'),
        Pattern(
            '/mnt/subvol2/.borgmatic-1234/mnt/subvol2/.borgmatic-1234',
            Pattern_type.NO_RECURSE,
            Pattern_style.FNMATCH,
        ),
    ]
    assert config == {
        'btrfs': {},
        'exclude_patterns': ['/bar'],
    }


def test_remove_data_source_dumps_deletes_snapshots():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2',
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol1/.borgmatic-*/mnt/subvol1')
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol2/.borgmatic-*/mnt/subvol2')
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1',
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'),
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2',
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'),
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2',
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs',
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs',
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1',
    ).once()
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs',
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).once()
    flexmock(module).should_receive('delete_snapshot').with_args(
        'btrfs',
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2',
    ).never()
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678',
    ).and_return(True)
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol1/.borgmatic-1234',
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol1/.borgmatic-5678',
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol2/.borgmatic-1234',
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args(
        '/mnt/subvol2/.borgmatic-5678',
    ).never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_without_hook_configuration_bails():
    flexmock(module).should_receive('get_subvolumes').never()
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=None,
        config={'source_directories': '/mnt/subvolume'},
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_get_subvolumes_file_not_found_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_raise(FileNotFoundError)
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_get_subvolumes_called_process_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_raise(
        module.subprocess.CalledProcessError(1, 'command', 'error'),
    )
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_dry_run_skips_deletes():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2',
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol1/.borgmatic-*/mnt/subvol1')
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol2/.borgmatic-*/mnt/subvol2')
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1',
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'),
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2',
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'),
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2',
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=True,
    )


def test_remove_data_source_dumps_without_subvolumes_skips_deletes():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(())
    flexmock(module).should_receive('make_snapshot_path').never()
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_without_snapshots_skips_deletes():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2',
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol1/.borgmatic-*/mnt/subvol1')
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol2/.borgmatic-*/mnt/subvol2')
    flexmock(module.glob).should_receive('glob').and_return(())
    flexmock(module.os.path).should_receive('isdir').never()
    flexmock(module).should_receive('delete_snapshot').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_delete_snapshot_file_not_found_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2',
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol1/.borgmatic-*/mnt/subvol1')
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol2/.borgmatic-*/mnt/subvol2')
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1',
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'),
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2',
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'),
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2',
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').and_raise(FileNotFoundError)
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_delete_snapshot_called_process_error_bails():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (
            module.Subvolume('/mnt/subvol1', contained_patterns=(Pattern('/mnt/subvol1'),)),
            module.Subvolume('/mnt/subvol2', contained_patterns=(Pattern('/mnt/subvol2'),)),
        ),
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol1').and_return(
        '/mnt/subvol1/.borgmatic-1234/./mnt/subvol1',
    )
    flexmock(module).should_receive('make_snapshot_path').with_args('/mnt/subvol2').and_return(
        '/mnt/subvol2/.borgmatic-1234/./mnt/subvol2',
    )
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol1/.borgmatic-*/mnt/subvol1')
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/mnt/subvol2/.borgmatic-*/mnt/subvol2')
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol1/.borgmatic-*/mnt/subvol1',
    ).and_return(
        ('/mnt/subvol1/.borgmatic-1234/mnt/subvol1', '/mnt/subvol1/.borgmatic-5678/mnt/subvol1'),
    )
    flexmock(module.glob).should_receive('glob').with_args(
        '/mnt/subvol2/.borgmatic-*/mnt/subvol2',
    ).and_return(
        ('/mnt/subvol2/.borgmatic-1234/mnt/subvol2', '/mnt/subvol2/.borgmatic-5678/mnt/subvol2'),
    )
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-1234/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol1/.borgmatic-5678/mnt/subvol1',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-1234/mnt/subvol2',
    ).and_return(True)
    flexmock(module.os.path).should_receive('isdir').with_args(
        '/mnt/subvol2/.borgmatic-5678/mnt/subvol2',
    ).and_return(False)
    flexmock(module).should_receive('delete_snapshot').and_raise(
        module.subprocess.CalledProcessError(1, 'command', 'error'),
    )
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_root_subvolume_skips_duplicate_removal():
    config = {'btrfs': {}}
    flexmock(module).should_receive('get_subvolumes').and_return(
        (module.Subvolume('/', contained_patterns=(Pattern('/etc'),)),),
    )

    flexmock(module).should_receive('make_snapshot_path').with_args('/').and_return(
        '/.borgmatic-1234',
    )

    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).with_args(
        '/.borgmatic-1234',
        temporary_directory_prefix=module.BORGMATIC_SNAPSHOT_PREFIX,
    ).and_return('/.borgmatic-*')

    flexmock(module.glob).should_receive('glob').with_args('/.borgmatic-*').and_return(
        ('/.borgmatic-1234', '/.borgmatic-5678'),
    )

    flexmock(module.os.path).should_receive('isdir').with_args('/.borgmatic-1234').and_return(
        True,
    ).and_return(False)
    flexmock(module.os.path).should_receive('isdir').with_args('/.borgmatic-5678').and_return(
        True,
    ).and_return(False)

    flexmock(module).should_receive('delete_snapshot').with_args('btrfs', '/.borgmatic-1234').once()
    flexmock(module).should_receive('delete_snapshot').with_args('btrfs', '/.borgmatic-5678').once()

    flexmock(module.os.path).should_receive('isdir').with_args('').and_return(False)

    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps(
        hook_config=config['btrfs'],
        config=config,
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )
